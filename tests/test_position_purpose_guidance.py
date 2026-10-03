"""Runtime delivery boundaries for position/purpose editorial contracts.

These are loader invariants. A model's actual prose and original-source reading
require separate artifact review; keyword scores cannot establish that behavior.
"""
from pathlib import Path
import shutil
import tempfile
import unittest
from unittest.mock import patch

from research_assistant import guidance


ROLES = ("writer", "reviewer", "coordinator", "literature", "simulation", "mechanism")


class PositionPurposeGuidanceTests(unittest.TestCase):
    def test_actual_selected_bodies_follow_scope_without_expanding_other_jobs(self):
        root = guidance.resource_root()
        source = (root / "skills/scientific-writing/references" /
                  guidance.LIBRARY_REFERENCE).read_text(encoding="utf-8")
        expected = {
            "title_abstract": ["selection-contract", "abstract-opening", "model-introduction"],
            "introduction": ["selection-contract", "introduction-bridge", "model-introduction"],
            "methods_results": ["selection-contract", "model-introduction"],
            "discussion_conclusions": ["selection-contract"],
            "full_manuscript": ["selection-contract", "abstract-opening", "introduction-bridge", "model-introduction"],
        }
        bodies = {}
        for anchor in expected["full_manuscript"]:
            marker = f'<a id="{anchor}"></a>'
            bodies[anchor] = source.split(marker, 1)[1].split('<a id="', 1)[0].strip()
        for role in ROLES:
            for section, anchors in expected.items():
                with self.subTest(role=role, section=section):
                    scope = {"mode": "audit", "sections": [section]}
                    self.assertEqual(guidance.library_reference_anchors(scope), anchors)
                    loaded = guidance.load_role(role, scope)
                    for anchor, body in bodies.items():
                        self.assertEqual(body in loaded, anchor in anchors)
                        self.assertEqual(loaded.count(f'<a id="{anchor}"></a>'), int(anchor in anchors))
            unscoped = guidance.load_role(role)
            for body in bodies.values():
                self.assertNotIn(body, unscoped)

    def test_combined_scope_deduplicates_contract_and_retains_existing_evidence_route(self):
        combined = {"mode": "revise", "sections": ["title_abstract", "introduction", "methods_results"]}
        loaded = guidance.load_role("writer", combined)
        for anchor in guidance.library_reference_anchors(combined):
            self.assertEqual(loaded.count(f'<a id="{anchor}"></a>'), 1)
        self.assertEqual(loaded.count('<a id="evidence-medium"></a>'), 1)
        for section in ("title_abstract", "introduction"):
            selected = guidance.load_role("writer", {"mode": "revise", "sections": [section]})
            self.assertNotIn('<a id="evidence-medium"></a>', selected)

    def test_relocated_resource_tree_loads_without_external_library_or_developer_paths(self):
        original = guidance.resource_root()
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory) / "portable"
            for name in ("roles", "skills"):
                shutil.copytree(original / name, root / name)
            scope = {"mode": "draft", "sections": ["introduction"]}
            with patch.object(guidance, "resource_root", return_value=root):
                loaded = guidance.load_role("writer", scope)
            self.assertNotIn(str(original), loaded)
            self.assertIn(str(root), loaded)
            self.assertIn('<a id="selection-contract"></a>', loaded)
            self.assertIn('<a id="introduction-bridge"></a>', loaded)

    def test_missing_or_ambiguous_contract_anchor_fails_instead_of_silent_omission(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "skills/scientific-writing/references" / guidance.LIBRARY_REFERENCE
            path.parent.mkdir(parents=True)
            path.write_text('# Provenance\n<a id="selection-contract"></a>\nA\n'
                            '<a id="selection-contract"></a>\nB\n', encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "Missing or duplicate writing reference anchor"):
                guidance.reference_text(guidance.LIBRARY_REFERENCE, root, anchors=["selection-contract"])
            with self.assertRaisesRegex(ValueError, "Missing or duplicate writing reference anchor"):
                guidance.reference_text(guidance.LIBRARY_REFERENCE, root, anchors=["abstract-opening"])


if __name__ == "__main__":
    unittest.main()
