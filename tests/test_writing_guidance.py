"""Explicit distribution and feedback, not a proxy for literary quality."""
import asyncio
import copy
import json
from pathlib import Path
import re
import tempfile
import unittest
from unittest.mock import patch

from research_assistant import guidance, schemas, state
from research_assistant.demo import DemoProvider
from research_assistant.engine import ExecutionError, Session, run_project, validate
from research_assistant.providers import _strict_output_schema, _canonicalize_optional_fields


SCOPE = {"mode": "revise", "sections": ["introduction"]}


class GuidanceTests(unittest.TestCase):
    def test_transport_schema_strictifies_nested_optional_selection_without_public_changes(self):
        original = copy.deepcopy(schemas.PLAN)
        strict = _strict_output_schema(schemas.PLAN)
        contract = strict["properties"]["tasks"]["items"]
        self.assertIn("writing", contract["required"])
        self.assertEqual(contract["properties"]["writing"]["anyOf"][1], {"type": "null"})
        self.assertEqual(schemas.PLAN, original)
        self.assertNotIn("writing", schemas.CONTRACT["required"])
        legacy = DemoProvider.contract("old", "writer", [], "manuscript")
        transport = {**legacy, "writing": None}
        validate(transport, contract)
        canonical = _canonicalize_optional_fields({"tasks": [transport]}, schemas.PLAN)
        self.assertEqual(canonical["tasks"], [legacy])
        validate(canonical["tasks"][0], schemas.CONTRACT)
        selected = {**legacy, "writing": SCOPE}
        self.assertEqual(_canonicalize_optional_fields(selected, schemas.CONTRACT), selected)
        self.assertEqual(_canonicalize_optional_fields({"reassessment": None}, schemas.DECISION), {"reassessment": None})

    def test_explicit_scope_selects_role_and_section_without_full_guide(self):
        instructions = guidance.load_role("writer", SCOPE)
        self.assertIn("# Scientific Editor", instructions)
        self.assertIn("# Scientific Writing Core", instructions)
        self.assertIn("# Introduction", instructions)
        self.assertNotIn("# Title and Abstract", instructions)
        self.assertNotIn("# Methods and Results", instructions)
        self.assertNotIn("# Discussion and Conclusions", instructions)
        self.assertNotIn("# Writing Review", instructions)
        self.assertNotIn("# Argument and intended readers", instructions)
        self.assertIn("# Scientific objects and sentence continuity", instructions)
        self.assertNotIn("# Chapter responsibilities and evidence-dependent writing", instructions)

    def test_compact_methods_are_delivered_to_scoped_roles_only(self):
        for role in ("writer", "reviewer", "literature", "mechanism", "simulation", "coordinator"):
            with self.subTest(role=role):
                scoped = guidance.load_role(role, SCOPE)
                self.assertIn("Assigned writing method source:", scoped)
                self.assertIn("# Scientific objects and sentence continuity", scoped)
                self.assertNotIn("# Scientific objects and sentence continuity", guidance.load_role(role))
        full = {"mode": "audit", "sections": ["full_manuscript"]}
        self.assertIn("# Chapter responsibilities and evidence-dependent writing", guidance.load_role("reviewer", full))
        self.assertIn("# Chapter responsibilities and evidence-dependent writing", guidance.load_role("coordinator", SCOPE))

    def test_missing_reference_fails_instead_of_silent_skipping(self):
        with tempfile.TemporaryDirectory() as directory:
            with self.assertRaisesRegex(ValueError, "Missing bundled writing reference"):
                guidance.reference_text("object-and-continuity.md", Path(directory))

    def test_nonwriting_roles_are_compact_and_do_not_infer_keywords(self):
        for role in ("coordinator", "simulation", "literature", "mechanism", "reviewer"):
            self.assertNotIn("# Scientific Writing Core", guidance.load_role(role))
        self.assertIn("# Scientific Writing Core", guidance.load_role("writer"))
        self.assertNotIn("# Introduction", guidance.load_role("writer"))
        with tempfile.TemporaryDirectory() as directory:
            session = Session(directory, None, brief="introduction title abstract discussion")
            request = session.request("literature", {"question": "search introduction papers"}, schemas.REVIEW, "q")
            self.assertNotIn("# Scientific Writing Core", request["instructions"])

    def test_full_manuscript_and_role_specific_audit(self):
        scope = {"mode": "audit", "sections": ["full_manuscript"]}
        self.assertEqual(set(guidance.selected_skills("reviewer", scope)),
                         {"scientific-writing", "paper-writing-review", *guidance.SECTIONS.values()})
        self.assertNotIn("scientific-editor", guidance.selected_skills("reviewer", scope))
        self.assertIn("scientific-editor", guidance.selected_skills("coordinator", SCOPE))

    def test_invalid_selection_is_rejected_before_state_commit(self):
        for scope in ({"mode": "guess", "sections": ["introduction"]},
                      {"mode": "draft", "sections": []},
                      {"mode": "draft", "sections": ["full_manuscript", "introduction"]},
                      {"mode": "draft", "sections": ["introduction", "introduction"]}):
            with self.subTest(scope=scope), tempfile.TemporaryDirectory() as directory:
                state.initialize(directory, "Write a bounded introduction")
                contract = DemoProvider.contract("W", "writer", [], "manuscript")
                contract["writing"] = scope
                before = state.context(directory)["revision"]
                with self.assertRaises(state.GovernanceError):
                    state.task(directory, contract)
                self.assertEqual(state.context(directory)["revision"], before)

    def test_old_and_selected_contract_schema_and_context_roundtrip(self):
        with tempfile.TemporaryDirectory() as directory:
            state.initialize(directory, "Write a bounded introduction")
            old = DemoProvider.contract("old", "literature", [], "source-notes")
            validate(old, schemas.CONTRACT)
            state.task(directory, old)
            selected = DemoProvider.contract("W", "writer", [], "manuscript")
            selected["writing"] = copy.deepcopy(SCOPE)
            validate(selected, schemas.CONTRACT)
            state.task(directory, selected)
            self.assertEqual(state.context(directory, "W")["task"]["writing"], SCOPE)
            self.assertNotIn("writing", state.context(directory, "old")["task"])

    def test_packaged_resource_precedence_and_progressive_links(self):
        root = guidance.resource_root()
        for skill in guidance.selected_skills("writer", {"mode": "audit", "sections": ["full_manuscript"]}):
            path = root / "skills" / skill / "SKILL.md"
            for link in re.findall(r"\]\(([^)]+)\)", path.read_text(encoding="utf-8")):
                self.assertTrue((path.parent / link.split("#")[0]).is_file(), (path, link))
        with tempfile.TemporaryDirectory() as directory:
            module = Path(directory) / "package" / "guidance.py"
            bundled = module.parent / "resources"
            (bundled / "roles").mkdir(parents=True)
            (bundled / "skills").mkdir()
            with patch.object(guidance, "__file__", str(module)):
                self.assertEqual(guidance.resource_root(), bundled)


class GuidanceWorkflowTests(unittest.IsolatedAsyncioTestCase):
    async def test_consequential_feedback_reaches_next_attempt_and_changed_report_blocks(self):
        class RepairProvider:
            def __init__(inner):
                inner.requests = []

            async def ask(inner, request):
                inner.requests.append(copy.deepcopy(request))
                packet = json.loads(request["prompt"])
                root = Path(request["cwd"])
                if request["request_id"].startswith("plan:"):
                    contract = DemoProvider.contract("W", "writer", [], "manuscript")
                    contract["writing"] = SCOPE
                    contract["budget"] = {"max_attempts": 2, "max_no_progress": 2}
                    return {"action": "complete" if packet["tasks"] else "work", "reason": "Located editorial repair",
                        "plan": {"reason": "Repair a scoped text", "facts": [], "hypotheses": [], "uncertainties": [],
                                 "next_decision": "Review source support", "claims": []},
                        "tasks": [] if packet["tasks"] else [contract],
                        "deliverables": ["manuscript/intro.md"] if packet["tasks"] else []}
                if request["role"] == "writer":
                    attempt = packet["next_attempt"]
                    path = root / "manuscript/intro.md"
                    path.parent.mkdir(exist_ok=True)
                    path.write_text("An explicitly bounded design motivation." if attempt == 2 else "An overbroad design motivation.", encoding="utf-8")
                    return {"attempt": attempt, "changed_understanding": False, "reason": "Editorial repair only",
                        "evidence": [{"path": "manuscript/intro.md", "level": "observation", "kind": "observation",
                                      "claim_ids": [], "summary": "Located editorial draft"}], "blockers": [],
                        "contribution": {"answer": "Draft supplied", "effect_on_project": "Reader scope clarified",
                                         "uncertainties": [], "next_options": [], "cost_note": "Fixture"}}
                if request["role"] == "reviewer":
                    first = request["request_id"].endswith(":1")
                    return {"summary": "Scope needs repair" if first else "Located repair checked", "findings": [
                        {"blocking": True, "claim_ids": [], "reason": "Narrow unsupported generality in opening",
                         "evidence_paths": ["manuscript/intro.md"]}] if first else [], "limitations": ["Fixture"]}
                first = packet["handoff"]["latest_result"]["attempt"] == 1
                return {"action": "continue" if first else "accept", "reason": "Use located review for one bounded repair",
                        "promotions": [], "resolutions": [], "claim_updates": [], "reassessment": None}

        with tempfile.TemporaryDirectory() as directory:
            provider = RepairProvider()
            result = await run_project(directory, provider, brief="Repair introduction", parallel=1)
            self.assertEqual(result["status"], "complete")
            second = next(r for r in provider.requests if r["request_id"] == "worker:W:2")
            feedback = json.loads(second["prompt"])["review_feedback"]
            self.assertIn("Narrow unsupported", feedback["report"]["findings"][0]["reason"])
            self.assertEqual(Path(feedback["path"]), Path("reviews/W/attempt-1.json"))
            self.assertTrue(state.audit(directory)["protocol_ok"])
            latest = Path(directory) / "reviews/W/attempt-2.json"
            latest.write_text("{}", encoding="utf-8")
            session = Session(directory, provider, parallel=1)
            with self.assertRaises(ExecutionError):
                session.review_feedback("W")

    async def test_scope_reaches_actual_worker_reviewer_and_disposition(self):
        class ScopedDemo(DemoProvider):
            def __init__(inner):
                super().__init__()
                inner.requests = []

            async def ask(inner, request):
                inner.requests.append(copy.deepcopy(request))
                response = await super().ask(request)
                if request["request_id"].startswith("plan:"):
                    for contract in response["tasks"]:
                        if contract["role"] == "writer":
                            contract["writing"] = copy.deepcopy(SCOPE)
                return response

        with tempfile.TemporaryDirectory() as directory:
            provider = ScopedDemo()
            result = await run_project(directory, provider, brief="Scoped writing protocol", parallel=2)
            self.assertEqual(result["status"], "complete")
            worker = next(r for r in provider.requests if r["request_id"] == "worker:T-write:1")
            review = next(r for r in provider.requests if r["request_id"] == "review:T-write:1")
            disposition = next(r for r in provider.requests if r["request_id"] == "decide:T-write:1")
            for request in (worker, review, disposition):
                self.assertIn("# Introduction", request["instructions"])
                self.assertNotIn("# Methods and Results", request["instructions"])
                self.assertIn("# Scientific objects and sentence continuity", request["instructions"])
            self.assertIn("# Writing Review", review["instructions"])
            self.assertIn("# Scientific Editor", disposition["instructions"])
            self.assertNotIn("# Scientific Editor", review["instructions"])
            plan = [r for r in provider.requests if r["request_id"].startswith("plan:")][-1]
            feedback = next(x for x in json.loads(plan["prompt"])["returns"] if x["task_id"] == "T-write")["review_feedback"]
            self.assertTrue((Path(directory) / feedback["path"]).is_file())
            self.assertTrue(state.audit(directory)["protocol_ok"])

    async def test_saved_calls_keep_original_instructions_but_changed_inputs_fail(self):
        class Provider:
            calls = 0

            async def ask(inner, request):
                inner.calls += 1
                return {"summary": "Old response", "findings": [], "limitations": []}

        with tempfile.TemporaryDirectory() as directory:
            provider = Provider()
            session = Session(directory, provider, brief="Saved bounded request")
            packet = {"question": "Assess scope", "writing": SCOPE}
            await session.ask("reviewer", packet, schemas.REVIEW, "saved")
            old = copy.deepcopy(session.data["calls"]["saved"]["request"])
            with patch("research_assistant.engine.role_text", return_value="Updated guide version"):
                response = await session.ask("reviewer", packet, schemas.REVIEW, "saved")
            self.assertEqual(response["summary"], "Old response")
            self.assertEqual(provider.calls, 1)
            self.assertEqual(session.data["calls"]["saved"]["request"], old)
            changed = {**packet, "writing": {"mode": "revise", "sections": ["discussion_conclusions"]}}
            with self.assertRaises(ExecutionError):
                await session.ask("reviewer", changed, schemas.REVIEW, "saved")
            self.assertEqual(provider.calls, 1)


if __name__ == "__main__":
    unittest.main()
