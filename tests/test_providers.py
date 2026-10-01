"""Provider failure boundaries without launching a model or an external job."""

import asyncio
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
                return self

            async def run(self):
                await asyncio.sleep(sdk.delay)
                if sdk.failure:
                    raise sdk.failure
                return SimpleNamespace(final_response=sdk.response, status=sdk.status, error=None)

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

    async def test_turn_timeout_requests_interrupt_and_closes_client(self):
        sdk = FakeSDK(delay=1)
        with self.sdk_patch(sdk), self.assertRaisesRegex(ProviderError, "deadline"):
            await CodexProvider(timeout_seconds=0.01).ask(self.request)
        self.assertTrue(sdk.clients[0].interrupted)
        self.assertTrue(sdk.clients[0].closed)

    async def test_startup_timeout_also_closes_client(self):
        sdk = FakeSDK()
        sdk.start_delay = 1
        with self.sdk_patch(sdk), self.assertRaisesRegex(ProviderError, "deadline"):
            await CodexProvider(timeout_seconds=0.01).ask(self.request)
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

    def test_invalid_deadline_is_rejected(self):
        for value in (0, -1, True, float("inf"), float("nan")):
            with self.subTest(value=value), self.assertRaises(ValueError):
                CodexProvider(timeout_seconds=value)


if __name__ == "__main__":
    unittest.main()
