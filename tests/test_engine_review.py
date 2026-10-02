"""Independent adversarial checks for provider/MAF scientific handoffs."""

import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_assistant import schemas, state
from research_assistant import cli, engine
from research_assistant.demo import DemoProvider
from research_assistant.engine import Collector, ExecutionError, Session, execution_lock, role_text, run_project, validate


class CountingProvider:
    def __init__(self, response=None, error=None):
        self.count = 0
        self.requests = []
        self.response = response if response is not None else {"answer": "unknown"}
        self.error = error
        self.thread_ids = {}

    async def ask(self, request):
        self.count += 1
        self.requests.append(copy.deepcopy(request))
        self.thread_ids[request["request_id"]] = f"test-thread-{self.count}"
        if self.error:
            raise self.error
        return copy.deepcopy(self.response)


class FakeContext:
    def __init__(self):
        self.messages = []

    async def send_message(self, message, *, target_id):
        self.messages.append((message, target_id))


SIMPLE_SCHEMA = {
    "type": "object", "properties": {"answer": {"type": "string"}},
    "required": ["answer"], "additionalProperties": False,
}


def report(path="output/evidence.txt", claim_ids=None):
    return {
        "attempt": 1, "changed_understanding": True,
        "reason": "A negative result changed which explanation should be tested.",
        "evidence": [{"path": path, "level": "observation", "kind": "negative",
                      "claim_ids": claim_ids or [], "summary": "No support under the stated conditions."}],
        "blockers": [],
        "contribution": {"answer": "not supported", "effect_on_project": "investigate an alternative",
                         "uncertainties": [], "next_options": ["test a competing explanation"],
                         "cost_note": "one test"},
    }


class EngineHandoffReview(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.addCleanup(self.temp.cleanup)

    def session(self, provider=None, **kwargs):
        return Session(self.root, provider or CountingProvider(), brief="Investigate bounded evidence.", **kwargs)

    def task(self, session, *, inputs=None, claim_ids=None):
        state.task(self.root, {
            "id": "trial", "role": "simulation", "question": "Can this observation discriminate the mechanism?",
            "purpose": "Rule out an unsupported explanation", "claim_ids": claim_ids or [],
            "inputs": inputs or [], "outputs": ["output/evidence.txt"], "writes": ["output"],
            "acceptance": ["Honest result with stated scope"],
            "budget": {"max_attempts": 1, "max_no_progress": 1}, "depends_on": [],
        })

    async def test_completed_request_is_not_reexecuted_after_reload(self):
        provider = CountingProvider()
        session = self.session(provider)
        expected = await session.ask("coordinator", {"question": "one"}, SIMPLE_SCHEMA, "request-1")
        recovered = Session(self.root, provider, parallel=2)
        result = await recovered.ask("coordinator", {"question": "one"}, SIMPLE_SCHEMA, "request-1")
        self.assertEqual(result, expected)
        self.assertEqual(provider.count, 1)
        self.assertEqual(recovered.data["calls"]["request-1"]["thread_id"], "test-thread-1")

    async def test_unknown_or_failed_call_never_replays_automatically(self):
        provider = CountingProvider(error=RuntimeError("crash after possible side effect"))
        session = self.session(provider)
        with self.assertRaises(RuntimeError):
            await session.ask("simulation", {"question": "one"}, SIMPLE_SCHEMA, "request-1")
        recovered = Session(self.root, provider)
        with self.assertRaisesRegex(ExecutionError, "unknown/failed"):
            await recovered.ask("simulation", {"question": "one"}, SIMPLE_SCHEMA, "request-1")
        self.assertEqual(provider.count, 1)

    async def test_completed_cache_cannot_be_used_for_changed_context_or_role(self):
        provider = CountingProvider()
        session = self.session(provider)
        await session.ask("coordinator", {"question": "one"}, SIMPLE_SCHEMA, "request-1")
        for role, packet in (("coordinator", {"question": "two"}), ("reviewer", {"question": "one"})):
            with self.subTest(role=role, packet=packet), self.assertRaises(ExecutionError):
                await session.ask(role, packet, SIMPLE_SCHEMA, "request-1")
        self.assertEqual(provider.count, 1)

    async def test_completed_result_cache_cannot_rebind_mutated_evidence(self):
        output = self.root / "output" / "evidence.txt"
        output.parent.mkdir()
        output.write_text("original negative observation", encoding="utf-8")
        provider = CountingProvider(response=report())
        session = self.session(provider)
        self.task(session)
        packet = session.worker_context("trial")
        await session.ask("simulation", packet, schemas.RESULT, "worker:trial:1")
        # Simulate the crash window before state.record, followed by an artifact edit.
        output.write_text("different conditions and outcome", encoding="utf-8")
        recovered = Session(self.root, provider)
        with self.assertRaises(ExecutionError):
            await recovered.ask("simulation", packet, schemas.RESULT, "worker:trial:1")
        self.assertEqual(provider.count, 1)
        self.assertEqual(state.context(self.root, "trial")["status"], "active")

    async def test_collector_rejects_artifact_changed_after_worker_return(self):
        output = self.root / "output" / "evidence.txt"
        output.parent.mkdir()
        output.write_text("original negative observation", encoding="utf-8")
        provider = CountingProvider(response=report())
        session = self.session(provider)
        self.task(session)
        packet = session.worker_context("trial")
        result = await session.ask("simulation", packet, schemas.RESULT, "worker:trial:1")
        output.write_text("different evidence while sibling is running", encoding="utf-8")
        collector = Collector(session)
        with self.assertRaises(ExecutionError):
            await collector.collect({"task_id": "trial", "batch_id": "batch-0", "batch_size": 1,
                                     "report": result}, FakeContext())
        self.assertEqual(state.context(self.root, "trial")["next_attempt"], 1)

    async def test_worker_evidence_outside_declared_writes_is_rejected(self):
        (self.root / "unassigned.txt").write_text("exists outside assigned writes", encoding="utf-8")
        provider = CountingProvider(response=report(path="unassigned.txt"))
        session = self.session(provider)
        self.task(session)
        with self.assertRaisesRegex(ExecutionError, "declared writes"):
            await session.ask("simulation", session.worker_context("trial"), schemas.RESULT, "worker:trial:1")
        self.assertEqual(session.data["calls"]["worker:trial:1"]["status"], "failed")

    async def test_reconciled_worker_result_is_bound_and_can_be_imported(self):
        provider = CountingProvider(error=RuntimeError("transport lost after work"))
        session = self.session(provider)
        self.task(session)
        packet = session.worker_context("trial")
        with self.assertRaises(RuntimeError):
            await session.ask("simulation", packet, schemas.RESULT, "worker:trial:1")
        output = self.root / "output" / "evidence.txt"
        output.parent.mkdir()
        output.write_text("inspected negative finding", encoding="utf-8")
        response_path = self.root / "inspected-response.json"
        response_path.write_text(json.dumps(report()), encoding="utf-8")
        with redirect_stdout(io.StringIO()):
            code = cli.main(["reconcile", str(self.root), "worker:trial:1", str(response_path),
                             "--reason", "Inspected original artifact and response after transport failure."])
        self.assertEqual(code, 0)
        recovered = Session(self.root, provider)
        self.assertIn("artifacts", recovered.data["calls"]["worker:trial:1"])
        result = await recovered.ask("simulation", packet, schemas.RESULT, "worker:trial:1")
        await Collector(recovered).collect({"task_id": "trial", "batch_id": "batch-0", "batch_size": 1,
                                           "report": result}, FakeContext())
        self.assertEqual(state.context(self.root, "trial")["status"], "awaiting_decision")
        self.assertEqual(provider.count, 1)

    async def test_worker_can_cite_frozen_input_without_owning_its_writes(self):
        source = self.root / "input.txt"
        source.write_text("Original source observations", encoding="utf-8")
        provider = CountingProvider(response=report(path="input.txt"))
        session = self.session(provider)
        self.task(session, inputs=[{"path": "input.txt"}])
        expected_revision = state.context(self.root, "trial")["task"]["inputs"][0]["revision"]
        result = await session.ask("simulation", session.worker_context("trial"), schemas.RESULT, "worker:trial:1")
        await Collector(session).collect({"task_id": "trial", "batch_id": "batch-0", "batch_size": 1,
                                          "report": result}, FakeContext())
        self.assertEqual(state.context(self.root, "trial")["latest_result"]["evidence"][0]["revision"], expected_revision)

    async def test_changed_frozen_input_cannot_be_rebound_as_new_evidence(self):
        source = self.root / "input.txt"
        source.write_text("Original observations", encoding="utf-8")
        provider = CountingProvider(response=report(path="input.txt"))
        session = self.session(provider)
        self.task(session, inputs=[{"path": "input.txt"}])
        packet = session.worker_context("trial")
        source.write_text("Changed during execution", encoding="utf-8")
        with self.assertRaisesRegex(ExecutionError, "changed frozen input"):
            await session.ask("simulation", packet, schemas.RESULT, "worker:trial:1")
        self.assertEqual(state.context(self.root, "trial")["next_attempt"], 1)

    async def test_explicit_external_input_is_valid_provenance(self):
        with tempfile.TemporaryDirectory() as external:
            source = Path(external) / "paper.txt"
            source.write_text("A separately stored original paper", encoding="utf-8")
            session = self.session(CountingProvider(response=report(path=str(source))))
            self.task(session, inputs=[{"path": str(source)}])
            result = await session.ask("simulation", session.worker_context("trial"), schemas.RESULT, "worker:trial:1")
            self.assertEqual(result["evidence"][0]["path"], str(source))
            self.assertTrue(state._fresh(self.root, session.data["calls"]["worker:trial:1"]["artifacts"][0]))

    async def test_changed_input_invalidates_return_even_when_not_cited(self):
        source = self.root / "input.txt"
        source.write_text("Original conditions", encoding="utf-8")
        output = self.root / "output" / "evidence.txt"
        output.parent.mkdir()
        output.write_text("Result from the original conditions", encoding="utf-8")
        session = self.session(CountingProvider(response=report()))
        self.task(session, inputs=[{"path": "input.txt"}])
        packet = session.worker_context("trial")
        source.write_text("New conditions while worker runs", encoding="utf-8")
        with self.assertRaisesRegex(ExecutionError, "changed frozen input"):
            await session.ask("simulation", packet, schemas.RESULT, "worker:trial:1")
        self.assertEqual(state.context(self.root, "trial")["next_attempt"], 1)

    async def test_native_resume_after_disposition_crash_does_not_repeat_workers(self):
        provider = DemoProvider()
        original = Session.dispose
        crashed = False

        async def crash_after_first_disposition(session, task_id):
            nonlocal crashed
            await original(session, task_id)
            if not crashed:
                crashed = True
                raise RuntimeError("process stopped after science transaction committed")

        with patch.object(Session, "dispose", crash_after_first_disposition):
            with self.assertRaises(Exception):
                await run_project(self.root, provider, brief="Protocol demo", parallel=2)
        prior_calls = list(provider.calls)
        result = await run_project(self.root, provider, resume=True, parallel=2)
        self.assertEqual(result["status"], "complete")
        for request_id in ("worker:T-evidence:1", "worker:T-background:1"):
            self.assertEqual(provider.calls.count(request_id), prior_calls.count(request_id))
        self.assertEqual(state.context(self.root)["claims"]["C1"]["status"], "parked")
        self.assertTrue(state.audit(self.root)["protocol_ok"])

    async def test_explicit_reopen_replans_after_missing_input_arrives(self):
        class NeedsInputProvider(CountingProvider):
            async def ask(inner, request):
                inner.count += 1
                inner.requests.append(copy.deepcopy(request))
                available = (self.root / "source.txt").is_file()
                return {
                    "action": "complete" if available else "needs_input",
                    "reason": "Required source arrived" if available else "Required source is missing",
                    "plan": {"reason": "Check required source", "facts": [], "hypotheses": [],
                             "uncertainties": [], "next_decision": "inspect source", "claims": []},
                    "tasks": [], "deliverables": ["source.txt"] if available else [],
                }

        provider = NeedsInputProvider()
        first = await run_project(self.root, provider, brief="Summarize the user-supplied source.")
        self.assertEqual(first["status"], "needs_input")
        (self.root / "source.txt").write_text("Actual newly supplied content", encoding="utf-8")
        again = await run_project(self.root, provider, resume=True, additional_cycles=1)
        self.assertEqual(again["status"], "complete")
        self.assertEqual(provider.count, 2)
        self.assertNotEqual(provider.requests[0]["request_id"], provider.requests[1]["request_id"])

    async def test_explicit_budget_extension_continues_without_repeating_workers(self):
        provider = DemoProvider()
        first = await run_project(self.root, provider, brief="Protocol demo", max_cycles=1)
        self.assertEqual(first["status"], "budget_reached")
        again = await run_project(self.root, provider, resume=True, additional_cycles=2)
        self.assertEqual(again["status"], "complete")
        self.assertEqual(provider.calls.count("worker:T-evidence:1"), 1)
        self.assertEqual(provider.calls.count("worker:T-background:1"), 1)

    async def test_invalid_schema_is_not_cached_as_success(self):
        provider = CountingProvider(response={"answer": "unknown", "invented": True})
        session = self.session(provider)
        with self.assertRaises(ExecutionError):
            await session.ask("literature", {"question": "one"}, SIMPLE_SCHEMA, "request-1")
        self.assertEqual(session.data["calls"]["request-1"]["status"], "failed")

    async def test_context_bound_rejects_before_external_call(self):
        provider = CountingProvider()
        session = self.session(provider, max_context_chars=10)
        with self.assertRaisesRegex(ExecutionError, "Context exceeds"):
            await session.ask("literature", {"question": "large contextual packet"}, SIMPLE_SCHEMA, "request-1")
        self.assertEqual(provider.count, 0)
        self.assertEqual(session.data["calls"], {})

    def test_worker_context_rejects_changed_input(self):
        source = self.root / "input.txt"
        source.write_text("original conditions", encoding="utf-8")
        session = self.session()
        self.task(session, inputs=[{"path": "input.txt"}])
        source.write_text("changed conditions", encoding="utf-8")
        with self.assertRaisesRegex(ExecutionError, "changed inputs"):
            session.worker_context("trial")

    def test_context_omits_unrelated_claims_and_full_event_history(self):
        session = self.session()
        state.plan(self.root, {"reason": "Define two different claims", "claims": [
            {"id": "C1", "statement": "Relevant hypothesis"},
            {"id": "C2", "statement": "Unrelated hypothesis"},
        ]})
        self.task(session, claim_ids=["C1"])
        packet = session.worker_context("trial")
        self.assertEqual(set(packet["claims"]), {"C1"})
        self.assertNotIn("events", packet)
        self.assertEqual(packet["task"]["writes"], ["output"])

    def test_claim_scope_rejects_outsider_without_partial_record(self):
        session = self.session()
        state.plan(self.root, {"reason": "Define two different claims", "claims": [
            {"id": "C1", "statement": "Relevant hypothesis"},
            {"id": "C2", "statement": "Unrelated hypothesis"},
        ]})
        self.task(session, claim_ids=["C1"])
        output = self.root / "output" / "evidence.txt"
        output.parent.mkdir()
        output.write_text("negative result", encoding="utf-8")
        with self.assertRaises(state.GovernanceError):
            state.record(self.root, "trial", report(claim_ids=["C2"]))
        self.assertEqual(state.context(self.root, "trial")["next_attempt"], 1)

    def test_schema_does_not_accept_boolean_as_attempt_number(self):
        value = report()
        value["attempt"] = True
        with self.assertRaises(ExecutionError):
            validate(value, schemas.RESULT)

    def test_local_and_packaged_skills_reach_role_instructions(self):
        session = self.session()
        request = session.request("simulation", {"question": "bounded"}, SIMPLE_SCHEMA, "task-1")
        self.assertIn("# Simulation Evidence", request["instructions"])
        self.assertIn("Applicable skill source:", request["instructions"])
        self.assertIn("Resolve linked references relative", request["instructions"])
        # Exercise the installed-wheel layout without relying on repo fallback.
        package = self.root / "package"
        role_dir = package / "resources" / "roles"
        skill_dir = package / "resources" / "skills" / "simulation-evidence"
        role_dir.mkdir(parents=True)
        skill_dir.mkdir(parents=True)
        (role_dir / "simulation.md").write_text("Packaged simulation role", encoding="utf-8")
        (skill_dir / "SKILL.md").write_text("Packaged skill instructions", encoding="utf-8")
        with patch.object(engine.guidance, "__file__", str(package / "guidance.py")):
            text = role_text("simulation")
        self.assertIn("Packaged simulation role", text)
        self.assertIn("Packaged skill instructions", text)
        self.assertIn(str(skill_dir / "SKILL.md"), text)

    def test_nested_execution_lock_rejects_second_runner(self):
        session = self.session()
        with execution_lock(session.directory):
            with self.assertRaises(ExecutionError):
                with execution_lock(session.directory):
                    self.fail("second runner acquired same project lock")

    async def test_rejected_runner_never_constructs_or_saves_session(self):
        session = self.session()
        session.save()
        saved = session.path.read_text(encoding="utf-8")
        with execution_lock(session.directory), patch("research_assistant.engine.Session") as constructor:
            with self.assertRaises(ExecutionError):
                await run_project(self.root, CountingProvider(), resume=True)
            constructor.assert_not_called()
        self.assertEqual(session.path.read_text(encoding="utf-8"), saved)


if __name__ == "__main__":
    unittest.main()
