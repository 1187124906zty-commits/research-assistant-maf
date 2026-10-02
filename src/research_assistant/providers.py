"""Optional local model providers, independent of the MAF workflow engine."""

from __future__ import annotations

import asyncio
import copy
import importlib
import inspect
import json
import math
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Protocol

from .progress import (best_candidate_question, checked_decision, default_decision,
                       diagnostic_question, parse_reports)


class ProviderError(RuntimeError):
    """A provider could not produce a usable structured response."""


class Provider(Protocol):
    async def ask(self, request: dict[str, Any]) -> dict[str, Any]:
        """Return a structured result for one independently scoped task."""


def _reject_constant(value: str) -> None:
    raise ValueError(f"Non-JSON constant {value}")


def _finite_float(value: str) -> float:
    parsed = float(value)
    if not math.isfinite(parsed):
        raise ValueError("JSON number exceeds finite Python float range")
    return parsed


def _unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"Duplicate JSON field {key!r}")
        result[key] = value
    return result


def _strict_output_schema(schema: dict) -> dict:
    """Codex transport requires every object property, using null for omission.

    The public/offline schema and durable request remain unchanged. Optional
    properties become required nullable only at this provider boundary.
    """
    result = copy.deepcopy(schema)
    if "anyOf" in result:
        result["anyOf"] = [_strict_output_schema(item) for item in result["anyOf"]]
    if "items" in result:
        result["items"] = _strict_output_schema(result["items"])
    if "properties" in result:
        required = set(result.get("required", []))
        properties = {}
        for key, item in result["properties"].items():
            item = _strict_output_schema(item)
            properties[key] = item if key in required else {"anyOf": [item, {"type": "null"}]}
        result["properties"] = properties
        result["required"] = list(properties)
    return result


def _canonicalize_optional_fields(value: Any, schema: dict) -> Any:
    """Remove transport-only nulls, preserving required nulls and all evidence."""
    if "anyOf" in schema:
        variants = schema["anyOf"]
        for variant in variants:
            if ((isinstance(value, dict) and variant.get("type") == "object")
                    or (isinstance(value, list) and variant.get("type") == "array")):
                return _canonicalize_optional_fields(value, variant)
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        required = set(schema.get("required", []))
        return {key: _canonicalize_optional_fields(item, properties.get(key, {}))
                for key, item in value.items()
                if not (key in properties and key not in required and item is None)}
    if isinstance(value, list):
        return [_canonicalize_optional_fields(item, schema.get("items", {})) for item in value]
    return value


class CodexProvider:
    """Run each request in a fresh local Codex SDK thread.

    The optional ``openai-codex`` dependency controls a local app-server and
    reuses the user's existing Codex authentication. This adapter does not read,
    copy, change, or log credential files. With no ``codex_bin`` override, the
    SDK selects its bundled, version-matched runtime. Model and sandbox options
    are omitted so the runtime retains its configured defaults; the SDK's
    default approval policy applies.

    ``cwd`` selects the task workspace, not an OS confinement boundary. Codex
    can use tools and write wherever the host's actual permissions allow.
    Prompts, fresh threads and structured output do not enforce filesystem
    isolation. ``timeout_seconds`` is an active-turn progress interval, not a
    deadline. It asks for public diagnostic feedback without cancelling work.
    Startup transport has a separate timeout. Explicit caller cancellation
    requests interruption, without guaranteeing that external solvers stop.

    ``last_thread_id`` is diagnostic only. Concurrent callers should use
    ``thread_ids[request_id]`` to avoid attributing another task's thread.
    """

    def __init__(self, codex_bin: str | None = None, timeout_seconds: float = 600,
                 *, startup_timeout_seconds: float = 60, progress_callback=None):
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be a finite positive number")
        if (isinstance(startup_timeout_seconds, bool)
                or not isinstance(startup_timeout_seconds, (int, float))
                or not math.isfinite(startup_timeout_seconds) or startup_timeout_seconds <= 0):
            raise ValueError("startup_timeout_seconds must be a finite positive number")
        if progress_callback is not None and not callable(progress_callback):
            raise ValueError("progress_callback must be callable or None")
        if codex_bin is not None and (not isinstance(codex_bin, str) or not codex_bin.strip()):
            raise ValueError("codex_bin must be a nonempty executable path or None")
        self.codex_bin = codex_bin
        self.timeout_seconds = float(timeout_seconds)
        self.startup_timeout_seconds = float(startup_timeout_seconds)
        self.progress_callback = progress_callback
        self.progress_records: dict[str, list[dict]] = {}
        self.last_thread_id: str | None = None
        self.thread_ids: dict[str, str] = {}

    async def _progress_event(self, request_id: str, kind: str, **details):
        event = {"request_id": request_id, "kind": kind,
                 "thread_id": self.thread_ids.get(request_id), **details}
        self.progress_records.setdefault(request_id, []).append(event)
        if self.progress_callback is None:
            return None
        try:
            value = self.progress_callback(copy.deepcopy(event))
            if inspect.isawaitable(value):
                value = await value
            return checked_decision(value) if kind == "diagnostic_report" else None
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # An observer error must not turn slow scientific work into a kill.
            self.progress_records[request_id].append({"request_id": request_id,
                "kind": "callback_error", "error_type": type(exc).__name__})
            return None

    async def _steer(self, turn, request_id: str, kind: str, text: str, **details):
        await self._progress_event(request_id, kind, question=text, **details)
        try:
            await asyncio.wait_for(turn.steer(text), timeout=self.startup_timeout_seconds)
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            # Failed status feedback does not cancel the running model turn.
            await self._progress_event(request_id, "steer_error", error_type=type(exc).__name__)

    async def _collect_turn(self, turn, request_id: str, asked: dict) -> Any:
        """One public stream consumer; reasoning notifications are ignored."""
        final, fallback, completed = None, None, None
        reports = []
        handed_off = False
        stream = turn.stream()
        try:
            async for event in stream:
                payload = event.payload
                if event.method == "item/completed" and getattr(payload, "turn_id", None) == turn.id:
                    item = payload.item
                    item = getattr(item, "root", item)
                    if getattr(item, "type", None) != "agentMessage":
                        continue
                    phase = getattr(item, "phase", None)
                    phase = getattr(phase, "value", phase)
                    text = getattr(item, "text", "")
                    if phase == "final_answer":
                        final = text
                    elif phase is None:
                        fallback = text
                    if phase == "commentary":
                        for report in parse_reports(text):
                            number = report["checkpoint"]
                            if number not in asked["numbers"] or number in asked["answered"]:
                                continue
                            asked["answered"].add(number)
                            reports.append(report)
                            override = await self._progress_event(request_id, "diagnostic_report", report=report)
                            decision = override or default_decision(reports)
                            await self._progress_event(request_id, "coordinator_decision", decision=decision,
                                                       checkpoint=number)
                            if decision["action"] == "request_best_candidate" and not handed_off:
                                handed_off = True
                                await self._steer(turn, request_id, "best_candidate_question",
                                    best_candidate_question(decision["reason"]), checkpoint=number,
                                    evidence=decision["evidence"])
                elif event.method == "turn/completed" and getattr(payload.turn, "id", None) == turn.id:
                    completed = payload.turn
        finally:
            await stream.aclose()
        if completed is None:
            raise ProviderError("Codex turn completed event was not received")
        return SimpleNamespace(status=completed.status, error=completed.error,
                               final_response=final if final is not None else fallback)

    async def _active_turn(self, turn, request_id: str) -> Any:
        asked = {"numbers": set(), "answered": set()}
        collector = asyncio.create_task(self._collect_turn(turn, request_id, asked))
        checkpoint = 0
        try:
            while True:
                done, _ = await asyncio.wait({collector}, timeout=self.timeout_seconds)
                if done:
                    return await collector
                checkpoint += 1
                asked["numbers"].add(checkpoint)
                for number in sorted(asked["numbers"] - asked["answered"] - {checkpoint}):
                    # Explicit unknown state remains visible; silence is not repetition.
                    if number == checkpoint - 1:
                        await self._progress_event(request_id, "diagnostic_unanswered", checkpoint=number,
                            decision={"action": "continue", "reason": "No public diagnostic answer yet; keep work active."})
                await self._steer(turn, request_id, "diagnostic_question",
                                  diagnostic_question(checkpoint), checkpoint=checkpoint)
        finally:
            if not collector.done():
                collector.cancel()
                try:
                    await collector
                except asyncio.CancelledError:
                    pass

    async def wait_for_turn(self, turn, request_id: str) -> Any:
        """Monitor an existing SDK turn without owning its client lifecycle.

        The caller keeps the client open. Explicit cancellation still requests
        interruption; a progress interval alone does not cancel the turn.
        """
        try:
            return await self._active_turn(turn, request_id)
        except asyncio.CancelledError:
            try:
                await asyncio.wait_for(turn.interrupt(), timeout=5)
            except Exception:
                pass
            raise

    @staticmethod
    def _load_sdk() -> tuple[Any, Any]:
        try:
            sdk = importlib.import_module("openai_codex")
            return sdk.AsyncCodex, sdk.CodexConfig
        except (ImportError, AttributeError) as exc:
            raise ProviderError(
                "The Codex provider requires a compatible openai-codex Python "
                "SDK. Install the project's codex optional dependency."
            ) from exc

    @staticmethod
    def _check_request(request: dict[str, Any]) -> None:
        if not isinstance(request, dict):
            raise ValueError("provider request must be a dict")
        for field in ("role", "instructions", "prompt", "cwd", "request_id"):
            if not isinstance(request.get(field), str):
                raise ValueError(f"request.{field} must be a string")
        for field in ("role", "prompt", "cwd", "request_id"):
            if not request[field].strip():
                raise ValueError(f"request.{field} must not be empty")
        workspace = Path(request["cwd"])
        if not workspace.is_absolute() or not workspace.is_dir():
            raise ValueError("request.cwd must be an existing absolute directory")
        if not isinstance(request.get("output_schema"), dict) or not request["output_schema"]:
            raise ValueError("request.output_schema must be a nonempty JSON schema dict")
        try:
            json.dumps(request["output_schema"], allow_nan=False)
        except (TypeError, ValueError) as exc:
            raise ValueError("request.output_schema must contain valid JSON values") from exc

    async def _execute(self, request: dict[str, Any], sdk_factory: Any, config_class: Any) -> Any:
        # No overrides of model, authentication, approval, sandbox, or Codex home.
        config = config_class(codex_bin=self.codex_bin) if self.codex_bin else config_class()
        client = sdk_factory(config=config)
        turn = None
        try:
            # thread_start initializes lazily. close() in finally also covers a
            # cancelled startup, when context entry would not have completed.
            async def startup():
                thread = await client.thread_start(
                    cwd=request["cwd"],
                    developer_instructions=(
                        f"Research role: {request['role']}\n"
                        f"Request identifier: {request['request_id']}\n\n"
                        f"{request['instructions']}"
                    ),
                )
                thread_id = getattr(thread, "id", None)
                if isinstance(thread_id, str):
                    self.last_thread_id = thread_id
                    self.thread_ids[request["request_id"]] = thread_id
                return await thread.turn(request["prompt"],
                    output_schema=_strict_output_schema(request["output_schema"]))
            try:
                turn = await asyncio.wait_for(startup(), timeout=self.startup_timeout_seconds)
            except TimeoutError as exc:
                await self._progress_event(request["request_id"], "startup_timeout",
                                           timeout_seconds=self.startup_timeout_seconds)
                raise ProviderError("Codex startup transport exceeded its separate timeout; "
                                    "no active turn handle is available. Check existing jobs before retrying.") from exc
            return await self._active_turn(turn, request["request_id"])
        except asyncio.CancelledError:
            if turn is not None:
                try:
                    # Best effort only; cancellation must not wait indefinitely
                    # for the app-server to acknowledge interruption.
                    await asyncio.wait_for(turn.interrupt(), timeout=5)
                except Exception:
                    pass
            raise
        finally:
            await client.close()

    async def ask(self, request: dict[str, Any]) -> dict[str, Any]:
        self._check_request(request)
        sdk_factory, config_class = self._load_sdk()
        request_id = request["request_id"]
        try:
            result = await self._execute(request, sdk_factory, config_class)
        except Exception as exc:
            raise ProviderError(f"Codex request {request_id!r} failed: {exc}") from exc

        status = getattr(result, "status", None)
        status = getattr(status, "value", status)
        error = getattr(result, "error", None)
        if status != "completed" or error is not None:
            raise ProviderError(
                f"Codex request {request_id!r} did not complete successfully "
                f"(status={status!r})"
            )
        response = getattr(result, "final_response", None)
        if not isinstance(response, str) or not response.strip():
            raise ProviderError(f"Codex request {request_id!r} returned no final JSON response")
        try:
            parsed = json.loads(
                response,
                parse_constant=_reject_constant,
                parse_float=_finite_float,
                object_pairs_hook=_unique_object,
            )
        except (ValueError, TypeError) as exc:
            raise ProviderError(
                f"Codex request {request_id!r} returned malformed JSON: {exc}"
            ) from exc
        if not isinstance(parsed, dict):
            raise ProviderError(f"Codex request {request_id!r} returned a JSON value other than an object")
        # The SDK receives the schema; the workflow validates its own research
        # contract before accepting the returned object as scientific state.
        return _canonicalize_optional_fields(parsed, request["output_schema"])
