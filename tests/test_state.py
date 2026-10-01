"""Behavioral protocol tests, including the two opposite failure modes."""

import copy
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from research_assistant.state import GovernanceError, audit, context, decide, initialize, plan, record, snapshot, task
from research_assistant import state as runtime


class ResearchRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        initialize(self.root, "Which mechanism explains transport?", {"claims": [{"id": "C1", "statement": "The discretization resolves the trend"}, {"id": "C2", "statement": "The boundary condition explains the trend"}]})
        (self.root / "input.txt").write_text("fixed inputs, units SI", encoding="utf-8")

    def tearDown(self):
        self.tmp.cleanup()

    def contract(self, tid="T1", claims=None, **changes):
        data = {"id": tid, "role": "simulation", "question": "Does refinement change the conclusion?", "purpose": "Decide the next paper-relevant comparison", "claim_ids": claims or ["C1"], "inputs": [{"path": "input.txt"}], "outputs": [f"results/{tid}/"], "acceptance": ["Report QoI sensitivity and whether mechanism ranking changes"], "budget": {"max_attempts": 2, "max_no_progress": 1}, "depends_on": []}
        data.update(changes)
        return data

    def result(self, tid="T1", attempt=1, changed=True, claims=None, level="numerical_verification", kind="support", blockers=None):
        path = self.root / f"results/{tid}/{attempt}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(f"measured trend for {tid} attempt {attempt}", encoding="utf-8")
        return {"attempt": attempt, "changed_understanding": changed, "reason": "Comparison distinguishes plausible explanations" if changed else "Extra refinement did not change the decision", "evidence": [{"path": str(path.relative_to(self.root)), "level": level, "kind": kind, "claim_ids": claims or ["C1"], "summary": "QoI trend with uncertainty reported"}], "blockers": blockers or []}

    def promote(self, cid="C1", level="numerical_verification"):
        return {"action": "accept", "reason": "Evidence answers the requester question", "promotions": [{"claim_id": cid, "level": level, "evidence_indices": [0], "reason": "This exact comparison supports only the numerical statement"}]}

    def test_valid_path_accept_is_not_support(self):
        task(self.root, self.contract())
        result = record(self.root, "T1", self.result())
        self.assertTrue(result["evidence"][0]["revision"].startswith("sha256:"))
        decide(self.root, "T1", {"action": "accept", "reason": "Useful handoff received"})
        self.assertEqual(context(self.root)["claims"]["C1"]["status"], "hypothesis")
        self.assertTrue(audit(self.root)["protocol_ok"])

    def test_invalid_second_contract_does_not_partially_dispatch_batch(self):
        before = context(self.root)
        journal = (self.root / ".research-assistant" / "events.jsonl").read_text(encoding="utf-8")
        update = {"reason": "Prepare two ready tasks", "facts": ["A proposed but uncommitted fact"],
                  "claims": [{"id": "C3", "statement": "New proposal"}]}
        bad = self.contract("T2", claims=["unknown"])
        with self.assertRaises(GovernanceError):
            runtime.dispatch_batch(self.root, update, [self.contract(), bad])
        self.assertEqual(context(self.root), before)
        self.assertEqual((self.root / ".research-assistant" / "events.jsonl").read_text(encoding="utf-8"), journal)
        committed = runtime.dispatch_batch(self.root, update, [self.contract(), self.contract("T2")])
        self.assertEqual(committed["revision"], before["revision"] + 1)
        self.assertEqual(set(committed["tasks"]), {"T1", "T2"})

    def test_exact_evidence_promotion_and_scope(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result())
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", self.promote(level="physical_validation"))
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", self.promote(cid="C2"))
        decide(self.root, "T1", self.promote())
        self.assertEqual(context(self.root)["claims"]["C1"]["status"], "supported")
        self.assertEqual(set(context(self.root)["claims"]["C1"]["support"]), {"numerical_verification"})

    def test_negative_result_is_normal_handoff(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result(kind="negative"))
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", self.promote())
        decide(self.root, "T1", {"action": "reframe", "reason": "Negative outcome rules out this candidate", "claim_updates": [{"claim_id": "C1", "status": "invalidated", "reason": "Predicted change was not observed"}]})
        self.assertTrue(audit(self.root)["protocol_ok"])

    def test_no_progress_requires_reasoned_strategy_change(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result(changed=False))
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", {"action": "continue", "reason": "Try finer again"})
        decide(self.root, "T1", {"action": "continue", "reason": "Use a discriminating comparison", "reassessment": {"reason": "Mesh is not the unresolved issue", "strategy_change": "Compare boundary formulations", "additional_attempts": 0}})
        record(self.root, "T1", self.result(attempt=2, changed=False))
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", {"action": "continue", "reason": "Keep trying", "reassessment": {"reason": "More needed", "strategy_change": "Another test", "additional_attempts": 0}})
        decide(self.root, "T1", {"action": "park", "reason": "Question answered enough to prioritize a different mechanism"})

    def test_budget_extension_is_explicit(self):
        task(self.root, self.contract(budget={"max_attempts": 1, "max_no_progress": 2}))
        record(self.root, "T1", self.result())
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", {"action": "continue", "reason": "More accuracy"})
        decide(self.root, "T1", {"action": "continue", "reason": "One correction can discriminate alternatives", "reassessment": {"reason": "New boundary evidence", "strategy_change": "Run corrected boundary only", "additional_attempts": 1}})
        record(self.root, "T1", self.result(attempt=2))

    def test_stale_evidence_and_missing_files_are_detected(self):
        task(self.root, self.contract())
        report = self.result()
        record(self.root, "T1", report)
        (self.root / report["evidence"][0]["path"]).write_text("changed result", encoding="utf-8")
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", self.promote())
        codes = {risk["code"] for risk in audit(self.root)["risks"]}
        self.assertTrue({"stale_evidence", "unclosed_handoff"} <= codes)
        (self.root / "input.txt").unlink()
        self.assertFalse(context(self.root, "T1")["task"]["inputs"][0]["fresh"])

    def test_dependency_requires_disposition_and_validated_scope(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result())
        next_contract = self.contract("T2", depends_on=["T1"])
        with self.assertRaises(GovernanceError):
            task(self.root, next_contract)
        decide(self.root, "T1", self.promote())
        task(self.root, next_contract)
        with self.assertRaises(GovernanceError):
            task(self.root, self.contract("T3", claims=["C2"], depends_on=[{"task_id": "T1", "claim_ids": ["C2"], "required_level": "physical_validation"}]))

    def test_unit_blocker_blocks_only_its_claim(self):
        task(self.root, self.contract(claims=["C1", "C2"]))
        report = self.result(claims=["C2"], blockers=[{"claim_ids": ["C1"], "kind": "units", "reason": "Boundary flux has incompatible units"}])
        record(self.root, "T1", report)
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", self.promote("C1"))
        decide(self.root, "T1", self.promote("C2"))
        state = context(self.root)
        self.assertEqual(state["claims"]["C2"]["status"], "supported")
        task(self.root, self.contract("T2", claims=["C2"], depends_on=[{"task_id": "T1", "claim_ids": ["C2"], "required_level": "numerical_verification"}]))
        self.assertEqual(audit(self.root)["risks"][0]["claim_ids"], ["C1"])

    def test_new_counterevidence_invalidates_old_support(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result())
        decide(self.root, "T1", self.promote())
        task(self.root, self.contract("T2", depends_on=["T1"]))
        record(self.root, "T2", self.result("T2", kind="counterevidence"))
        self.assertEqual(context(self.root)["claims"]["C1"]["status"], "invalidated")
        with self.assertRaises(GovernanceError):
            decide(self.root, "T2", self.promote())
        decide(self.root, "T2", {"action": "reframe", "reason": "New test contradicts our previous interpretation"})
        with self.assertRaises(GovernanceError):
            task(self.root, self.contract("T3", depends_on=[{"task_id": "T2", "claim_ids": ["C1"], "required_level": "numerical_verification"}]))

    def test_task_context_recovers_research_thinking(self):
        plan(self.root, {"reason": "Pilot ruled out a previous explanation", "question": "Does boundary resistance explain the residual?", "facts": [{"text": "Ranking stable in pilot", "source": "pilot observation"}], "hypotheses": ["Boundary resistance dominates"], "uncertainties": ["Experimental boundary transfer unknown"], "next_decision": "Compare two boundary models", "target_journal": "Example engineering journal"})
        task(self.root, self.contract())
        ctx = context(self.root, "T1")
        self.assertEqual(ctx["research"]["next_decision"], "Compare two boundary models")
        self.assertNotIn("events", ctx)
        self.assertEqual(ctx["task"]["project_revision"], ctx["revision"] - 1)

    def test_worker_write_collision_and_identity(self):
        with self.assertRaises(GovernanceError):
            task(self.root, self.contract(), actor="worker")
        with self.assertRaises(GovernanceError):
            task(self.root, self.contract(outputs=[".research-assistant/research-state.json"]))
        task(self.root, self.contract())
        with self.assertRaises(GovernanceError):
            task(self.root, self.contract("T2", outputs=["results/T1/shared.txt"]))

    def test_pending_transaction_recovers_after_journal_failure(self):
        with mock.patch.object(runtime, "_append", side_effect=OSError("simulated interrupted append")):
            with self.assertRaises(OSError):
                plan(self.root, {"reason": "Updated understanding", "next_decision": "Discriminate mechanisms"})
        self.assertTrue((self.root / ".research-assistant/transaction.json").exists())
        report = audit(self.root)
        self.assertTrue(report["protocol_ok"])
        self.assertFalse((self.root / ".research-assistant/transaction.json").exists())
        self.assertEqual(context(self.root)["research"]["next_decision"], "Discriminate mechanisms")

    def test_snapshot_and_stale_input_refusal(self):
        locator = snapshot(self.root, ["input.txt"])[0]
        (self.root / "input.txt").write_text("new revision", encoding="utf-8")
        with self.assertRaises(GovernanceError):
            task(self.root, self.contract(inputs=[locator]))

    def test_input_change_denies_promotion_even_with_fresh_output(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result())
        (self.root / "input.txt").write_text("different boundary condition", encoding="utf-8")
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", self.promote())

    def test_dependency_counterevidence_propagates_only_to_affected_support(self):
        plan(self.root, {"reason": "Separate downstream question", "claims": [{"id": "C3", "statement": "Validated discretization explains the mechanism"}]})
        task(self.root, self.contract())
        record(self.root, "T1", self.result())
        decide(self.root, "T1", self.promote())
        dependency = {"task_id": "T1", "claim_ids": ["C1"], "required_level": "numerical_verification", "affects_claim_ids": ["C3"]}
        task(self.root, self.contract("T2", claims=["C3"], depends_on=[dependency]))
        record(self.root, "T2", self.result("T2", claims=["C3"]))
        decide(self.root, "T2", self.promote("C3"))
        task(self.root, self.contract("T3", claims=["C2"]))
        record(self.root, "T3", self.result("T3", claims=["C2"]))
        decide(self.root, "T3", self.promote("C2"))
        task(self.root, self.contract("T4"))
        record(self.root, "T4", self.result("T4", kind="counterevidence"))
        state = context(self.root)
        self.assertEqual(state["claims"]["C3"]["status"], "invalidated")
        self.assertEqual(state["claims"]["C2"]["status"], "supported")
        self.assertIn("invalid_dependency", {item["code"] for item in audit(self.root)["risks"]})

    def test_dependency_changes_before_decision_deny_promotion(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result())
        decide(self.root, "T1", self.promote())
        task(self.root, self.contract("T2", claims=["C2"], depends_on=[{"task_id": "T1", "claim_ids": ["C1"], "required_level": "numerical_verification"}]))
        record(self.root, "T2", self.result("T2", claims=["C2"]))
        task(self.root, self.contract("T3"))
        record(self.root, "T3", self.result("T3", kind="counterevidence"))
        with self.assertRaises(GovernanceError):
            decide(self.root, "T2", self.promote("C2"))

    def test_same_result_cannot_clear_its_own_unit_blocker(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result(blockers=[{"claim_ids": ["C1"], "kind": "units", "reason": "Units are wrong"}]))
        decision = self.promote()
        decision["resolutions"] = [{"claim_id": "C1", "challenge_id": "T1:1:blocker:0", "reason": "Calling old data correct", "evidence_indices": [0]}]
        with self.assertRaises(GovernanceError):
            decide(self.root, "T1", decision)
        decide(self.root, "T1", {"action": "continue", "reason": "Correct the unit conversion"})
        record(self.root, "T1", self.result(attempt=2))
        decision["resolutions"][0]["reason"] = "New conversion output uses consistent SI units"
        decide(self.root, "T1", decision)
        self.assertTrue(audit(self.root)["protocol_ok"])

    def test_retired_failure_is_retained_without_global_block(self):
        task(self.root, self.contract())
        record(self.root, "T1", self.result(blockers=[{"claim_ids": ["C1"], "kind": "units", "reason": "Cannot interpret magnitude in claimed units"}]))
        decide(self.root, "T1", {"action": "narrow", "reason": "Retire magnitude claim; preserve failure explicitly", "claim_updates": [{"claim_id": "C1", "status": "narrowed", "reason": "Magnitude assertion removed, trend remains a future new claim"}]})
        report = audit(self.root)
        self.assertTrue(report["protocol_ok"])
        self.assertTrue(report["risks"])
        self.assertFalse(report["risks"][0]["blocking"])
        self.assertFalse(context(self.root)["claims"]["C1"]["challenges"][0]["resolved"])

    def test_single_writer_lock_prevents_overlapping_transactions(self):
        with runtime._locked(self.root / ".research-assistant"):
            with self.assertRaises(GovernanceError):
                plan(self.root, {"reason": "Concurrent update", "next_decision": "Do not overwrite"})
        plan(self.root, {"reason": "After lock release", "next_decision": "Proceed"})
        self.assertTrue(audit(self.root)["protocol_ok"])

    def test_cli_end_to_end_and_audit_exit_codes(self):
        project = self.root / "cli-demo"
        project.mkdir()
        (project / "input.txt").write_text("conditions SI", encoding="utf-8")
        output = project / "results/T1/1.txt"
        output.parent.mkdir(parents=True)
        output.write_text("independent comparison", encoding="utf-8")
        config = self.root / "config.json"
        config.write_text(json.dumps({"claims": [{"id": "C1", "statement": "Numerical statement"}]}), encoding="utf-8")
        contract = self.root / "contract.json"
        contract.write_text(json.dumps(self.contract()), encoding="utf-8")
        report = self.root / "report.json"
        report.write_text(json.dumps({"attempt": 1, "changed_understanding": True, "reason": "Changed next mechanism test", "evidence": [{"path": "results/T1/1.txt", "level": "numerical_verification", "kind": "support", "claim_ids": ["C1"], "summary": "Numerical comparison"}], "blockers": []}), encoding="utf-8")
        decision = self.root / "decision.json"
        decision.write_text(json.dumps(self.promote()), encoding="utf-8")
        def command(*args, expected=0):
            completed = subprocess.run([sys.executable, "-m", "research_assistant.state_cli", *map(str, args)], capture_output=True, text=True)
            self.assertEqual(completed.returncode, expected, completed.stderr + completed.stdout)
            return json.loads(completed.stdout)
        command("init", project, "--question", "What explains the trend?", "--config", config)
        command("task", project, contract)
        command("record", project, "T1", report)
        self.assertFalse(command("audit", project, expected=2)["protocol_ok"])
        command("decide", project, "T1", decision)
        self.assertTrue(command("audit", project)["protocol_ok"])
        self.assertTrue(command("snapshot", project, "input.txt")[0]["revision"].startswith("sha256:"))


if __name__ == "__main__":
    unittest.main()
