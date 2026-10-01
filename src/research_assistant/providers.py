"""Optional local model providers, independent of the MAF workflow engine."""

from __future__ import annotations

import asyncio
import importlib
import json
import math
from pathlib import Path
from typing import Any, Protocol


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
    isolation. A deadline requests turn interruption and closes the SDK client;
    it does not guarantee termination of external solver processes.

    ``last_thread_id`` is diagnostic only. Concurrent callers should use
    ``thread_ids[request_id]`` to avoid attributing another task's thread.
    """

    def __init__(self, codex_bin: str | None = None, timeout_seconds: float = 600):
        if (
            isinstance(timeout_seconds, bool)
            or not isinstance(timeout_seconds, (int, float))
            or not math.isfinite(timeout_seconds)
            or timeout_seconds <= 0
        ):
            raise ValueError("timeout_seconds must be a finite positive number")
        if codex_bin is not None and (not isinstance(codex_bin, str) or not codex_bin.strip()):
            raise ValueError("codex_bin must be a nonempty executable path or None")
        self.codex_bin = codex_bin
        self.timeout_seconds = float(timeout_seconds)
        self.last_thread_id: str | None = None
        self.thread_ids: dict[str, str] = {}

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
            turn = await thread.turn(
                request["prompt"],
                output_schema=request["output_schema"],
            )
            return await turn.run()
        except asyncio.CancelledError:
            if turn is not None:
                try:
                    # Best effort only; the deadline must not wait indefinitely
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
            result = await asyncio.wait_for(
                self._execute(request, sdk_factory, config_class),
                timeout=self.timeout_seconds,
            )
        except TimeoutError as exc:
            raise ProviderError(
                f"Codex request {request_id!r} exceeded its "
                f"{self.timeout_seconds:g}-second deadline; interruption was "
                "requested where a turn handle was available. Check external "
                "jobs before retrying."
            ) from exc
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
        return parsed
