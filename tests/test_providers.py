"""Provider failure boundaries without launching a model or an external job."""

import asyncio
import json
from pathlib import Path
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from research_assistant.providers import CodexProvider, ProviderError


class FakeConfig:
    def __init__(self, **kwargs):
        self.kwargs = kwargs


class FakeSDK:
    def __init__(self, response='{"finding":"unresolved"}', delay=0, failure=None, status="completed"):
        self.response = response
        self.delay = delay
        self.failure = failure
        self.status = status
        self.clients = []
        self.start_delay = 0
        self.progress_reports = []
        self.steer_failure = None

    def factory(self, *, config):
        sdk = self

        class Client:
            closed = False
            interrupted = False

            async def thread_start(self, **kwargs):
                self.start_kwargs = kwargs
                await asyncio.sleep(sdk.start_delay)
                self.id = f"thread-{len(sdk.clients)}"
                return self

            async def turn(self, prompt, **kwargs):
                self.prompt = prompt
                self.turn_kwargs = kwargs
                self.queue = asyncio.Queue()
                self.steers = []
                return self

            async def steer(self, text):
                self.steers.append(text)
                if sdk.steer_failure is not None:
                    raise sdk.steer_failure
                if text.startswith("Progress checkpoint"):
                    number = sum(t.startswith("Progress checkpoint") for t in self.steers)
                    if number <= len(sdk.progress_reports):
                        report = {**sdk.progress_reports[number - 1], "checkpoint": number}
                        await self.queue.put("<research-progress>" + json.dumps(report) + "</research-progress>")

            def item_event(self, text, phase):
                item = SimpleNamespace(type="agentMessage", text=text, phase=phase)
                return SimpleNamespace(method="item/completed",
                    payload=SimpleNamespace(turn_id=self.id, item=item))

            async def stream(self):
                finish = asyncio.create_task(asyncio.sleep(sdk.delay))
                queued = None
                try:
                    while not finish.done():
                        queued = asyncio.create_task(self.queue.get())
                        done, _ = await asyncio.wait({finish, queued}, return_when=asyncio.FIRST_COMPLETED)
                        if queued in done:
                            yield self.item_event(queued.result(), "commentary")
                        else:
                            queued.cancel()
                            try:
                                await queued
                            except asyncio.CancelledError:
                                pass
                    if sdk.failure:
                        raise sdk.failure
                    yield self.item_event(sdk.response, "final_answer")
                    yield SimpleNamespace(method="turn/completed", payload=SimpleNamespace(
                        turn=SimpleNamespace(id=self.id, status=sdk.status, error=None)))
                finally:
                    finish.cancel()
                    if queued is not None and not queued.done():
                        queued.cancel()

            async def run(self):
                # Tests ensure the provider has only one stream consumer.
                raise AssertionError("Use stream once rather than run plus a second observer")

            async def interrupt(self):
                self.interrupted = True

            async def close(self):
                self.closed = True

        client = Client()
        client.config = config
        self.clients.append(client)
        return client


class CodexProviderTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.request = {
            "role": "simulation",
            "instructions": "Answer only the contracted question.",
            "prompt": "Assess the available evidence; do not launch new jobs.",
            "cwd": str(Path.cwd().resolve()),
            "output_schema": {
                "type": "object",
                "properties": {"finding": {"type": "string"}},
                "required": ["finding"],
                "additionalProperties": False,
            },
            "request_id": "task-1",
        }

    def sdk_patch(self, sdk):
        return patch.object(CodexProvider, "_load_sdk", return_value=(sdk.factory, FakeConfig))

    async def test_schema_forwarded_defaults_retained_and_thread_recorded(self):
        sdk = FakeSDK()
        provider = CodexProvider()
        with self.sdk_patch(sdk):
            result = await provider.ask(self.request)
        self.assertEqual(result, {"finding": "unresolved"})
        client = sdk.clients[0]
        self.assertEqual(client.config.kwargs, {})
        self.assertEqual(client.start_kwargs["cwd"], self.request["cwd"])
        self.assertIn(self.request["instructions"], client.start_kwargs["developer_instructions"])
        self.assertEqual(set(client.start_kwargs), {"cwd", "developer_instructions"})
        self.assertEqual(client.turn_kwargs, {"output_schema": self.request["output_schema"]})
        self.assertEqual(provider.thread_ids["task-1"], "thread-1")
        self.assertEqual(provider.last_thread_id, "thread-1")
        self.assertTrue(client.closed)

    async def test_each_request_starts_a_fresh_thread(self):
        sdk = FakeSDK()
        provider = CodexProvider(codex_bin="C:/configured/codex.exe")
        with self.sdk_patch(sdk):
            await provider.ask(self.request)
            await provider.ask({**self.request, "request_id": "task-2"})
        self.assertEqual(len(sdk.clients), 2)
        self.assertEqual(provider.thread_ids, {"task-1": "thread-1", "task-2": "thread-2"})
        self.assertEqual(sdk.clients[0].config.kwargs, {"codex_bin": "C:/configured/codex.exe"})

    async def test_malformed_or_ambiguous_json_is_rejected(self):
        for response in ('not JSON', '```json\n{}\n```', '{"finding":NaN}', '{"finding":1e999}', '{"finding":1,"finding":2}', '[]', 'null'):
            with self.subTest(response=response):
                sdk = FakeSDK(response=response)
                with self.sdk_patch(sdk), self.assertRaises(ProviderError):
                    await CodexProvider().ask(self.request)
                self.assertTrue(sdk.clients[0].closed)

    async def test_empty_final_response_is_rejected(self):
        for response in (None, "", "  "):
            with self.subTest(response=response):
                with self.sdk_patch(FakeSDK(response=response)), self.assertRaisesRegex(ProviderError, "no final JSON"):
                    await CodexProvider().ask(self.request)

    async def test_interrupted_turn_is_not_a_successful_delivery(self):
        with self.sdk_patch(FakeSDK(status="interrupted")), self.assertRaisesRegex(ProviderError, "did not complete"):
            await CodexProvider().ask(self.request)

    async def test_sdk_error_closes_client_and_preserves_cause(self):
        original = RuntimeError("runtime unavailable")
        sdk = FakeSDK(failure=original)
        with self.sdk_patch(sdk), self.assertRaisesRegex(ProviderError, "runtime unavailable") as raised:
            await CodexProvider().ask(self.request)
        self.assertIs(raised.exception.__cause__, original)
        self.assertTrue(sdk.clients[0].closed)

    @staticmethod
    def report(activity="slow_work", **kwargs):
        return {"activity": activity, "current_work": "Checking a source",
            "why_not_returned": "Original evidence needs inspection", "candidate": "results/current.json",
            "what_changed": "Working on necessary source verification", "remaining_evidence": ["Source section"],
            "new_evidence": True, "repetition_evidence": [], **kwargs}

    async def test_slow_active_turn_survives_checkpoint_and_returns(self):
        sdk = FakeSDK(delay=0.06)
        sdk.progress_reports = [self.report()]
        provider = CodexProvider(timeout_seconds=0.015)
        with self.sdk_patch(sdk):
            result = await provider.ask(self.request)
        self.assertEqual(result, {"finding": "unresolved"})
        self.assertFalse(sdk.clients[0].interrupted)
        self.assertTrue(sdk.clients[0].closed)
        records = provider.progress_records["task-1"]
        self.assertTrue(any(e["kind"] == "diagnostic_question" for e in records))
        self.assertTrue(any(e["kind"] == "diagnostic_report" for e in records))
        self.assertTrue(all(e["decision"]["action"] == "continue" for e in records if e["kind"] == "coordinator_decision"))

    async def test_silence_stays_running_and_is_observable(self):
        sdk = FakeSDK(delay=0.06)
        provider = CodexProvider(timeout_seconds=0.015)
        with self.sdk_patch(sdk):
            await provider.ask(self.request)
        self.assertFalse(sdk.clients[0].interrupted)
        self.assertFalse(any("Return the best current candidate" in text for text in sdk.clients[0].steers))
        self.assertTrue(any(e["kind"] == "diagnostic_unanswered" for e in provider.progress_records["task-1"]))

    async def test_status_transport_failure_does_not_cancel_the_active_turn(self):
        sdk = FakeSDK(delay=0.045)
        sdk.steer_failure = RuntimeError("steering transport unavailable")
        provider = CodexProvider(timeout_seconds=0.015)
        with self.sdk_patch(sdk):
            result = await provider.ask(self.request)
        self.assertEqual(result, {"finding": "unresolved"})
        self.assertFalse(sdk.clients[0].interrupted)
        self.assertTrue(any(e["kind"] == "steer_error" for e in provider.progress_records["task-1"]))

    async def test_evidenced_repetition_asks_question_before_candidate_handoff(self):
        sdk = FakeSDK(delay=0.065)
        repeated = self.report("repeated_polish", new_evidence=False,
            what_changed="No scientific evidence changed; wording was revised twice",
            repetition_evidence=["results/current.json revisions changed wording only"])
        sdk.progress_reports = [repeated, repeated]
        provider = CodexProvider(timeout_seconds=0.015)
        with self.sdk_patch(sdk):
            await provider.ask(self.request)
        records = provider.progress_records["task-1"]
        kinds = [e["kind"] for e in records]
        self.assertLess(kinds.index("diagnostic_question"), kinds.index("diagnostic_report"))
        self.assertLess(kinds.index("diagnostic_report"), kinds.index("best_candidate_question"))
        self.assertFalse(sdk.clients[0].interrupted)

    async def test_self_label_without_evidence_does_not_force_handoff(self):
        sdk = FakeSDK(delay=0.055)
        sdk.progress_reports = [self.report("repeated_polish", new_evidence=False)] * 2
        provider = CodexProvider(timeout_seconds=0.015)
        with self.sdk_patch(sdk):
            await provider.ask(self.request)
        self.assertFalse(any(e["kind"] == "best_candidate_question" for e in provider.progress_records["task-1"]))

    async def test_callback_can_provide_evidenced_decision_and_receives_all_events(self):
        sdk = FakeSDK(delay=0.05)
        sdk.progress_reports = [self.report()]
        observed = []
        async def coordinator(event):
            observed.append(event)
            if event["kind"] == "diagnostic_report":
                return {"action": "request_best_candidate", "reason": "Reviewed versions have no new evidence",
                        "evidence": ["results/current.json versions 2 and 3"]}
        provider = CodexProvider(timeout_seconds=0.015, progress_callback=coordinator)
        with self.sdk_patch(sdk):
            await provider.ask(self.request)
        self.assertTrue(any(e["kind"] == "best_candidate_question" for e in observed))
        self.assertFalse(sdk.clients[0].interrupted)

    async def test_callback_timer_only_request_is_rejected_without_cancellation(self):
        sdk = FakeSDK(delay=0.045)
        sdk.progress_reports = [self.report()]
        def coordinator(event):
            if event["kind"] == "diagnostic_report":
                return {"action": "request_best_candidate", "reason": "Too much time", "evidence": []}
        provider = CodexProvider(timeout_seconds=0.015, progress_callback=coordinator)
        with self.sdk_patch(sdk):
            await provider.ask(self.request)
        self.assertFalse(sdk.clients[0].interrupted)
        self.assertTrue(any(e["kind"] == "callback_error" for e in provider.progress_records["task-1"]))
        self.assertFalse(any(e["kind"] == "best_candidate_question" for e in provider.progress_records["task-1"]))

    async def test_startup_timeout_also_closes_client(self):
        sdk = FakeSDK()
        sdk.start_delay = 1
        with self.sdk_patch(sdk), self.assertRaisesRegex(ProviderError, "startup transport"):
            await CodexProvider(timeout_seconds=0.01, startup_timeout_seconds=0.01).ask(self.request)
        self.assertTrue(sdk.clients[0].closed)
        self.assertFalse(sdk.clients[0].interrupted)

    async def test_caller_cancellation_propagates_and_requests_interrupt(self):
        sdk = FakeSDK(delay=1)
        with self.sdk_patch(sdk):
            task = asyncio.create_task(CodexProvider().ask(self.request))
            while not sdk.clients or not hasattr(sdk.clients[0], "turn_kwargs"):
                await asyncio.sleep(0)
            task.cancel()
            with self.assertRaises(asyncio.CancelledError):
                await task
        self.assertTrue(sdk.clients[0].interrupted)
        self.assertTrue(sdk.clients[0].closed)

    async def test_invalid_request_rejected_before_sdk_import(self):
        for request in (
            {**self.request, "cwd": "relative/path"},
            {**self.request, "output_schema": {}},
            {**self.request, "prompt": ""},
            {**self.request, "request_id": 42},
        ):
            with self.subTest(request=request), patch.object(CodexProvider, "_load_sdk") as loader:
                with self.assertRaises(ValueError):
                    await CodexProvider().ask(request)
                loader.assert_not_called()

    async def test_optional_dependency_failure_is_actionable(self):
        with patch("research_assistant.providers.importlib.import_module", side_effect=ImportError("not installed")):
            with self.assertRaisesRegex(ProviderError, "optional dependency"):
                await CodexProvider().ask(self.request)

    def test_invalid_checkpoint_interval_is_rejected(self):
        for value in (0, -1, True, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CodexProvider(timeout_seconds=value)

    def test_invalid_startup_timeout_is_rejected(self):
        for value in (0, -1, True, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CodexProvider(startup_timeout_seconds=value)

    async def test_optional_transport_nulls_still_canonicalized(self):
        request = {**self.request, "output_schema": {"type": "object", "properties": {
            "finding": {"type": "string"}, "optional": {"type": "string"}},
            "required": ["finding"], "additionalProperties": False}}
        sdk = FakeSDK(response='{"finding":"unresolved","optional":null}')
        with self.sdk_patch(sdk):
            result = await CodexProvider().ask(request)
        self.assertEqual(result, {"finding": "unresolved"})
        self.assertEqual(sdk.clients[0].turn_kwargs["output_schema"]["required"], ["finding", "optional"])


if __name__ == "__main__":
    unittest.main()
