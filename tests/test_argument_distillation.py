"""Prompt routing and scientific counterexamples, never prose keyword scores."""
import importlib.util
import json
from pathlib import Path
import unittest

from research_assistant import guidance


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("distillation_cases", ROOT / "examples/argument-distillation/check_contracts.py")
cases_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cases_module)


class ArgumentDistillationTests(unittest.TestCase):
    def test_reader_task_routing_preserves_explicit_section_scope(self):
        intro = {"mode": "revise", "sections": ["introduction"]}
        methods = {"mode": "audit", "sections": ["methods_results"]}
        self.assertEqual(guidance.distillation_reference_anchors(intro),
                         ["reader-task", "language-and-trimming", "source-synthesis"])
        self.assertEqual(guidance.distillation_reference_anchors(methods),
                         ["reader-task", "language-and-trimming", "comparison-and-inference", "evidence-medium"])
        for role in ("writer", "reviewer", "coordinator", "literature", "simulation", "mechanism"):
            with self.subTest(role=role):
                scoped = guidance.load_role(role, methods)
                self.assertIn('<a id="comparison-and-inference"></a>', scoped)
                self.assertNotIn('<a id="source-synthesis"></a>', scoped)
                self.assertNotIn('<a id="reader-task"></a>', guidance.load_role(role))
        full = {"mode": "revise", "sections": ["full_manuscript"]}
        self.assertEqual(guidance.distillation_reference_anchors(full),
                         ["reader-task", "language-and-trimming", "source-synthesis",
                          "comparison-and-inference", "evidence-medium"])

    def test_evidence_medium_loader_delivers_body_only_for_assigned_sections(self):
        marker = '<a id="evidence-medium"></a>'
        heading = "## Allocate evidence between prose, displays and appendix"
        source = (guidance.resource_root() / "skills/scientific-writing/references" /
                  guidance.DISTILLATION_REFERENCE).read_text(encoding="utf-8")
        # Compare the delivered method, not only an anchor list or a linked skill.
        medium = source.split(marker, 1)[1].split('<a id="', 1)[0].strip()
        self.assertIn(heading, medium)
        expected = {
            "methods_results": True, "discussion_conclusions": True,
            "full_manuscript": True, "introduction": False, "title_abstract": False,
        }
        for role in ("writer", "reviewer", "coordinator", "literature", "simulation", "mechanism"):
            for section, included in expected.items():
                with self.subTest(role=role, section=section):
                    scope = {"mode": "audit", "sections": [section]}
                    loaded = guidance.load_role(role, scope)
                    self.assertEqual(loaded.count(marker), int(included))
                    self.assertEqual(heading in loaded, included)
                    self.assertEqual(medium in loaded, included)
            with self.subTest(role=role, section="no writing selection"):
                loaded = guidance.load_role(role)
                self.assertNotIn(marker, loaded)
                self.assertNotIn(heading, loaded)
                self.assertNotIn(medium, loaded)
        combined = {"mode": "revise", "sections": ["methods_results", "discussion_conclusions"]}
        self.assertEqual(guidance.distillation_reference_anchors(combined).count("evidence-medium"), 1)
        self.assertEqual(guidance.load_role("writer", combined).count(marker), 1)

    def test_ledger_keeps_actual_chapters_separate_from_adapted_targets(self):
        path = guidance.resource_root() / "skills/scientific-writing/references/distillation-source-ledger.json"
        ledger = json.loads(path.read_text(encoding="utf-8-sig"))
        records = {item["id"]: item for item in ledger["records"]}
        inverse = records["EXP-NMI-P007"]
        self.assertEqual(inverse["intended_section"], "Methods")
        self.assertEqual(inverse["actual_source_section"], "Discussion")
        self.assertEqual(inverse["doi"], "10.1038/s42256-023-00762-x")
        for record in records.values():
            self.assertTrue(record["actual_source_section"])
            self.assertTrue(record["transfer_boundary"])
            self.assertIsInstance(record["pdf_page"], int)

    def test_negative_claims_fail_and_changed_evidence_reverses_judgment(self):
        report = cases_module.run()
        self.assertEqual(report["case_count"], 8)
        for case in cases_module.cases():
            with self.subTest(case=case["id"]):
                self.assertEqual(cases_module.assess_claim(case["evidence"], case["positive"]), [])
                self.assertTrue(cases_module.assess_claim(case["evidence"], case["negative"]))
                if case["reversal"] is not None:
                    self.assertEqual(cases_module.assess_claim(case["reversal"], case["negative"]), [])

    def test_finite_candidate_set_never_proves_mathematical_uniqueness(self):
        fixture = next(case for case in cases_module.cases() if case["id"] == "selection_is_not_uniqueness")
        one_candidate = {**fixture["evidence"], "candidates": fixture["evidence"]["candidates"][:1]}
        self.assertEqual(cases_module.assess_claim(one_candidate, fixture["negative"]),
                         ["Finite candidate screening cannot establish uniqueness"])
        no_matching_candidate = {**fixture["evidence"], "candidates": []}
        self.assertEqual(cases_module.assess_claim(no_matching_candidate, fixture["negative"]),
                         ["Finite candidate screening cannot establish uniqueness"])
        self.assertEqual(cases_module.assess_claim(fixture["evidence"], fixture["negative"]),
                         ["Distinct matching parameter sets contradict uniqueness"])
        # False means no uniqueness claim. This is justified restraint even
        # with one candidate, rather than a theorem about the whole space.
        self.assertEqual(cases_module.assess_claim(one_candidate, fixture["positive"]), [])


if __name__ == "__main__":
    unittest.main()
