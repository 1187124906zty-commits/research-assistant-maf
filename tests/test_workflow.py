"""Exercise the actual MAF graph, persistence and command-line entry point."""
import asyncio
import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from research_assistant import state
from research_assistant.demo import DemoProvider
from research_assistant.engine import ExecutionError, run_project


class WorkflowTests(unittest.TestCase):
    def test_native_graph_parallel_handoff_negative_and_writing(self):
        with tempfile.TemporaryDirectory() as directory:
            provider = DemoProvider()
            result = asyncio.run(run_project(directory, provider, brief="Protocol demo", max_cycles=4))
            self.assertEqual(result["status"], "complete")
            self.assertEqual(result["cycles"], 2)
            self.assertTrue(result["checkpoint"])
            self.assertTrue(list((Path(directory)/".research-assistant/checkpoints").glob("*.json")))
            self.assertTrue((Path(directory)/"manuscript/report.md").is_file())
            current = state.context(directory)
            self.assertEqual(current["claims"]["C1"]["status"], "parked")
            self.assertEqual(current["claims"]["C1"]["support"], {})
            self.assertTrue(state.audit(directory)["protocol_ok"])
            events = result["events"]
            batch = next(event for event in events if event["kind"] == "batch_dispatched")
            self.assertEqual(len(batch["tasks"]), 2)
            self.assertIn("literature", [call["request"]["role"] for call in result["calls"].values()])
            count = len(provider.calls)
            again = asyncio.run(run_project(directory, provider, parallel=2, resume=True))
            self.assertEqual(again["status"], "complete")
            self.assertEqual(len(provider.calls), count)

    def test_session_budget_returns_without_accepting_science(self):
        with tempfile.TemporaryDirectory() as directory:
            result = asyncio.run(run_project(directory, DemoProvider(), brief="Protocol demo", max_cycles=1))
            self.assertEqual(result["status"], "budget_reached")
            self.assertEqual(state.context(directory)["claims"]["C1"]["support"], {})
            self.assertNotIn("T-write", state.context(directory)["tasks"])

    def test_provider_failure_preserves_other_outputs_without_replay(self):
        class FailOnce(DemoProvider):
            async def ask(self, request):
                if request["role"] == "simulation":
                    self.calls.append(request["request_id"])
                    raise RuntimeError("uncertain external completion")
                return await super().ask(request)
        with tempfile.TemporaryDirectory() as directory:
            provider = FailOnce()
            with self.assertRaises(Exception):
                asyncio.run(run_project(directory, provider, brief="Protocol demo"))
            calls = provider.calls.count("worker:T-evidence:1")
            with self.assertRaises(Exception):
                asyncio.run(run_project(directory, provider, resume=True))
            self.assertEqual(provider.calls.count("worker:T-evidence:1"), calls)
            ledger = state._load(Path(directory)/".research-assistant/execution.json")
            self.assertEqual(ledger["status"], "attention")
            self.assertEqual(ledger["calls"]["worker:T-evidence:1"]["status"], "failed")

    def test_real_cli_demo_and_status(self):
        with tempfile.TemporaryDirectory() as directory:
            run = subprocess.run([sys.executable, "-m", "research_assistant", "demo", directory],
                                 capture_output=True, text=True)
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout)["status"], "complete")
            status = subprocess.run([sys.executable, "-m", "research_assistant", "status", directory],
                                    capture_output=True, text=True)
            self.assertEqual(status.returncode, 0, status.stderr)
            self.assertTrue(json.loads(status.stdout)["audit"]["protocol_ok"])

    def test_legacy_console_encoding_does_not_report_completed_run_as_failure(self):
        with tempfile.TemporaryDirectory() as directory:
            asyncio.run(run_project(directory, DemoProvider(), brief="Protocol demo"))
            ledger_path = Path(directory) / ".research-assistant/execution.json"
            ledger = state._load(ledger_path)
            ledger["message"] = "A\u2212B\u7684\u5dee\u503c\u5df2\u6838\u5bf9"
            state._atomic(ledger_path, ledger)
            run = subprocess.run([sys.executable, "-m", "research_assistant", "status", directory],
                                 capture_output=True, env={**os.environ, "PYTHONIOENCODING": "gbk:strict"})
            self.assertEqual(run.returncode, 0, run.stderr)
            self.assertEqual(json.loads(run.stdout.decode("gbk"))["message"], ledger["message"])


if __name__ == "__main__":
    unittest.main()
