"""Bounded deterministic feedback corrects bookkeeping, never the evidence."""

import json
from pathlib import Path
import tempfile
import unittest

from research_assistant import state
from research_assistant.demo import DemoProvider
from research_assistant.engine import run_project


class PromotionProvider:
    def __init__(self, *, repeated_invalid=False, decision_error=False):
        self.requests = []
        self.repeated_invalid = repeated_invalid
        self.decision_error = decision_error
        self.science_before_decision = None

    async def ask(self, request):
        self.requests.append(request)
        packet = json.loads(request["prompt"])
        root = Path(request["cwd"])
        if request["role"] == "coordinator" and request["request_id"].startswith("plan:"):
            return {
                "action": "work" if not packet["tasks"] else "complete",
                "reason": "Assess a bounded numerical statement using actual artifacts",
                "plan": {"reason": "Choose a distinguishable statement", "facts": [], "hypotheses": [],
                         "uncertainties": ["No physical validation"], "next_decision": "interpret artifact",
                         "claims": [{"id": "C1", "statement": "The stated numerical check holds in its specified setting"}] if not packet["tasks"] else []},
                "tasks": [DemoProvider.contract("check", "simulation", ["C1"], "results")] if not packet["tasks"] else [],
                "deliverables": [] if not packet["tasks"] else ["results/check.txt"],
            }
        if request["role"] == "simulation":
            output = root / "results"
            output.mkdir(exist_ok=True)
            (output / "conditions.txt").write_text("Declared controlled numerical conditions", encoding="utf-8")
            (output / "check.txt").write_text("A scoped deterministic numerical check result", encoding="utf-8")
            return {
                "attempt": packet["next_attempt"], "changed_understanding": True,
                "reason": "Scoped numerical evidence was obtained",
                "evidence": [
                    {"path": "results/conditions.txt", "level": "observation", "kind": "observation",
                     "claim_ids": ["C1"], "summary": "Conditions are provenance, not numerical support"},
                    {"path": "results/check.txt", "level": "numerical_verification", "kind": "support",
                     "claim_ids": ["C1"], "summary": "Explicit support for this numerical statement only"},
                ], "blockers": [],
                "contribution": {"answer": "Scoped check completed", "effect_on_project": "enables bounded interpretation",
                                 "uncertainties": ["Real-world validity untested"], "next_options": [],
                                 "cost_note": "deterministic fixture"},
            }
        if request["role"] == "reviewer":
            return {"summary": "Scope and evidence roles remain explicit", "findings": [],
                    "limitations": ["Fixture only; no physical validity finding"]}
        if request["role"] == "coordinator":
            if self.decision_error:
                raise RuntimeError("transport interrupted; outcome uncertain")
            if self.science_before_decision is None:
                self.science_before_decision = state.context(root)["claims"]["C1"]
            corrected = ":correction:" in request["request_id"] and not self.repeated_invalid
            return {
                "action": "accept", "reason": "Accept numerical evidence at its exact scope",
                "promotions": [{"claim_id": "C1", "level": "numerical_verification",
                                "evidence_indices": [1] if corrected else [0, 1],
                                "reason": "Explicit supporting numerical evidence required"}],
                "resolutions": [], "claim_updates": [], "reassessment": None,
            }
        raise AssertionError("Unexpected role")


class BoundedFeedbackTests(unittest.IsolatedAsyncioTestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def role_requests(self, provider, prefix):
        return [request for request in provider.requests if request["request_id"].startswith(prefix)]

    async def test_semantic_promotion_error_gets_one_correction_and_completes(self):
        provider = PromotionProvider()
        result = await run_project(self.root, provider, brief="Interpret a numerical check", parallel=1)
        self.assertEqual(result["status"], "complete")
        decisions = self.role_requests(provider, "decide:")
        self.assertEqual([request["request_id"] for request in decisions], [
            "decide:check:1", "decide:check:1:correction:1",
        ])
        correction_packet = json.loads(decisions[1]["prompt"])
        correction_text = json.dumps(correction_packet)
        self.assertIn("exact requested validation level", correction_text)
        self.assertIn("evidence_indices", correction_text)
        self.assertEqual(len(self.role_requests(provider, "worker:")), 1)
        claim = state.context(self.root)["claims"]["C1"]
        self.assertEqual(claim["status"], "supported")
        self.assertEqual(set(claim["support"]), {"numerical_verification"})
        self.assertEqual([item["path"] for item in claim["support"]["numerical_verification"]], ["results/check.txt"])
        self.assertTrue(state.audit(self.root)["protocol_ok"])

    async def test_repeated_invalid_decisions_stop_without_science_changes_or_worker_replay(self):
        provider = PromotionProvider(repeated_invalid=True)
        with self.assertRaises(Exception):
            await run_project(self.root, provider, brief="Interpret a numerical check", parallel=1)
        self.assertEqual(len(self.role_requests(provider, "decide:")), 2)
        self.assertEqual(len(self.role_requests(provider, "worker:")), 1)
        self.assertEqual(state.context(self.root)["claims"]["C1"], provider.science_before_decision)
        self.assertEqual(state.context(self.root, "check")["status"], "awaiting_decision")
        before = len(provider.requests)
        with self.assertRaises(Exception):
            await run_project(self.root, provider, resume=True, parallel=1)
        self.assertEqual(len(provider.requests), before)
        self.assertEqual(state.context(self.root)["claims"]["C1"], provider.science_before_decision)
        self.assertEqual(state.context(self.root, "check")["next_attempt"], 2)

    async def test_provider_failure_never_triggers_semantic_correction(self):
        provider = PromotionProvider(decision_error=True)
        with self.assertRaises(Exception):
            await run_project(self.root, provider, brief="Interpret a numerical check", parallel=1)
        decisions = self.role_requests(provider, "decide:")
        self.assertEqual(len(decisions), 1)
        self.assertNotIn(":correction:", decisions[0]["request_id"])
        self.assertEqual(state.context(self.root)["claims"]["C1"]["support"], {})
        before = len(provider.requests)
        with self.assertRaises(Exception):
            await run_project(self.root, provider, resume=True, parallel=1)
        self.assertEqual(len(provider.requests), before)
        self.assertEqual(len(self.role_requests(provider, "worker:")), 1)

    async def test_correction_provider_failure_is_not_retried(self):
        class CorrectionTransportFailure(PromotionProvider):
            async def ask(inner, request):
                if ":correction:" in request["request_id"]:
                    inner.requests.append(request)
                    raise RuntimeError("correction transport lost; unknown completion")
                return await super().ask(request)

        provider = CorrectionTransportFailure()
        with self.assertRaises(Exception):
            await run_project(self.root, provider, brief="Interpret a numerical check", parallel=1)
        self.assertEqual(len(self.role_requests(provider, "decide:")), 2)
        self.assertEqual(state.context(self.root)["claims"]["C1"]["support"], {})
        before = len(provider.requests)
        with self.assertRaises(Exception):
            await run_project(self.root, provider, resume=True, parallel=1)
        self.assertEqual(len(provider.requests), before)
        self.assertEqual(len(self.role_requests(provider, "worker:")), 1)

    async def test_unscoped_blocking_review_is_feedback_not_automatic_acceptance(self):
        class UnscopedProvider(PromotionProvider):
            async def ask(inner, request):
                if request["role"] == "reviewer":
                    inner.requests.append(request)
                    return {"summary": "Reader/source defect remains", "findings": [
                        {"blocking": True, "claim_ids": [], "reason": "Missing readable scope explanation",
                         "evidence_paths": ["results/check.txt"]}], "limitations": []}
                if request["role"] == "coordinator" and request["request_id"].startswith("decide:"):
                    inner.requests.append(request)
                    correction = ":correction:" in request["request_id"]
                    return {"action": "park" if correction else "accept",
                            "reason": "Park pending an explicit new correction task" if correction else "Accept initial return",
                            "promotions": [], "resolutions": [], "claim_updates": [], "reassessment": None}
                return await super().ask(request)

        provider = UnscopedProvider()
        await run_project(self.root, provider, brief="Assess a bounded report", parallel=1, max_cycles=1)
        decisions = self.role_requests(provider, "decide:")
        self.assertEqual(len(decisions), 2)
        packet = json.loads(decisions[1]["prompt"])
        self.assertIn("Blocking unscoped", packet["guard_feedback"])
        self.assertEqual(state.context(self.root, "check")["status"], "parked")
        self.assertEqual(state.context(self.root)["claims"]["C1"]["support"], {})
        self.assertEqual(len(self.role_requests(provider, "worker:")), 1)


if __name__ == "__main__":
    unittest.main()
