"""Delivery and progressive disclosure invariants, not prose quality scores."""
import re
import unittest

from research_assistant import guidance


class CompactWritingTests(unittest.TestCase):
    def test_actual_load_is_bounded_and_examples_follow_scope(self):
        expected = {
            "title_abstract": ["abstract-example"],
            "introduction": ["introduction-example"],
            "methods_results": ["methods-example", "results-example"],
            "discussion_conclusions": ["results-example"],
            "full_manuscript": ["abstract-example", "introduction-example", "methods-example", "results-example"],
        }
        examples = guidance.reference_text(guidance.EXAMPLE_REFERENCE)
        for section, anchors in expected.items():
            scope = {"mode": "revise", "sections": [section]}
            loaded = guidance.load_role("writer", scope)
            self.assertEqual(guidance.example_reference_anchors(scope), anchors)
            self.assertLess(len(loaded), 52000 if section == "full_manuscript" else 36000)
            self.assertIn("All scientific content below is invented for teaching.", loaded)
            for anchor in expected["full_manuscript"]:
                marker = f'<a id="{anchor}"></a>'
                body = examples.split(marker, 1)[1].split('<a id="', 1)[0].strip()
                self.assertEqual(body in loaded, anchor in anchors)
                self.assertEqual(loaded.count(marker), int(anchor in anchors))
        self.assertNotIn("All scientific content below is invented for teaching.", guidance.load_role("writer"))

    def test_source_cards_preserve_location_and_route_without_external_library(self):
        expected = {"title_abstract": [], "introduction": ["ctx-001"],
                    "methods_results": ["ctx-003"], "discussion_conclusions": ["ctx-004"],
                    "full_manuscript": ["ctx-001", "ctx-003", "ctx-004"]}
        for section, anchors in expected.items():
            scope = {"mode": "draft", "sections": [section]}
            self.assertEqual(guidance.source_example_reference_anchors(scope), anchors)
            loaded = guidance.load_role("writer", scope)
            for anchor in ("ctx-001", "ctx-002", "ctx-003", "ctx-004", "ctx-005", "ctx-006"):
                self.assertEqual(loaded.count(f'<a id="{anchor}"></a>'), int(anchor in anchors))
            if anchors:
                self.assertIn("actual", loaded)
                self.assertIn("Illustrative adaptation, not a quotation or reported result.", loaded)
        # Existing direct callers still get a complete standalone chapter skill.
        complete = guidance.skill_text("paper-introduction")
        compact = guidance.skill_text("paper-introduction", compact_section=True)
        self.assertGreater(len(complete), len(compact))
        self.assertIn("# Introduction", compact)

    def test_special_operations_and_host_api_are_optional(self):
        scope = {"mode": "audit", "sections": ["full_manuscript"]}
        for role in ("writer", "reviewer", "coordinator", "simulation", "literature", "mechanism"):
            loaded = guidance.load_role(role, scope)
            self.assertNotIn("## Inverse candidates and constraints", loaded)
            self.assertNotIn("## Selection and optimization budgets", loaded)
            self.assertNotIn("create_thread", loaded)
            self.assertNotIn("candidates[].contract_assessment.status", loaded)
        for name in ("task-type-checks.md", "host-scheduling.md", "library-adapter.md"):
            self.assertGreater(len(guidance.reference_text(name)), 500)

    def test_all_local_reference_links_and_anchors_resolve(self):
        refs = guidance.resource_root() / "skills/scientific-writing/references"
        for path in refs.glob("*.md"):
            for target in re.findall(r'\]\(([^)]+)\)', path.read_text(encoding="utf-8")):
                if "://" in target:
                    continue
                filename, _, anchor = target.partition("#")
                destination = path.parent / filename if filename else path
                self.assertTrue(destination.is_file(), (path, target))
                if anchor:
                    self.assertIn(f'<a id="{anchor}"></a>', destination.read_text(encoding="utf-8"), (path, target))


if __name__ == "__main__":
    unittest.main()
