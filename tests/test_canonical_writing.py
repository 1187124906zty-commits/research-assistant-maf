"""Canonical host writing entry and standalone fallback, with unchanged contracts."""
import asyncio
import copy
import json
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from research_assistant import guidance, schemas, state
from research_assistant.demo import DemoProvider
from research_assistant.engine import Session, run_project


ENTRY = "---\nname: research-writing-skill\n---\n# Canonical writing entry\nSingle maintained test standard.\n"


class CanonicalWritingTests(unittest.TestCase):
    def test_implicit_host_entry_and_explicit_override_and_failures(self):
        with tempfile.TemporaryDirectory() as directory:
            home = Path(directory)
            entry = home / "skills/research-writing-skill/SKILL.md"
            with patch.dict(os.environ, {"CODEX_HOME": str(home)}, clear=True):
                self.assertIsNone(guidance.canonical_writing_skill())
                entry.parent.mkdir(parents=True)
                entry.write_text(ENTRY, encoding="utf-8")
                self.assertEqual(guidance.canonical_writing_skill(), entry.resolve())
                with patch.dict(os.environ, {"MAF_RESEARCH_WRITING_SKILL": str(home / "absent.md")}):
                    with self.assertRaisesRegex(ValueError, "Missing configured writing skill"):
                        guidance.canonical_writing_skill()
                entry.write_text("---\nname: another-skill\n---\n", encoding="utf-8")
                with self.assertRaisesRegex(ValueError, "Unexpected writing skill name"):
                    guidance.canonical_writing_skill()

    def test_skill_name_must_belong_to_frontmatter_not_body_examples(self):
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "SKILL.md"
            for body in ("---\nname: another-skill\n---\n```yaml\nname: research-writing-skill\n```\n",
                         "# Example\nname: research-writing-skill\n"):
                entry.write_text(body, encoding="utf-8")
                with self.subTest(body=body), patch.dict(os.environ, {"MAF_RESEARCH_WRITING_SKILL": str(entry)}):
                    with self.assertRaisesRegex(ValueError, "Unexpected writing skill name"):
                        guidance.canonical_writing_skill()
            entry.write_text(ENTRY.replace("name: research-writing-skill", "name: 'research-writing-skill'"), encoding="utf-8")
            with patch.dict(os.environ, {"MAF_RESEARCH_WRITING_SKILL": str(entry)}):
                self.assertEqual(guidance.canonical_writing_skill(), entry.resolve())

    def test_canonical_literature_scope_does_not_reintroduce_old_source_route(self):
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "SKILL.md"
            entry.write_text(ENTRY, encoding="utf-8")
            with patch.object(guidance, "canonical_writing_skill", return_value=entry):
                loaded = guidance.load_role("literature", {"mode": "revise", "sections": ["introduction"]})
            self.assertNotIn("scientific-writing reference source-use.md", loaded)
            self.assertIn("resource-selection reference linked by the maintained writing entry", loaded)

    def test_unscoped_automatic_writer_review_uses_same_entry_and_falls_back(self):
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "SKILL.md"
            entry.write_text(ENTRY, encoding="utf-8")
            session = Session(Path(directory) / "project", None, brief="Automatic writing review")
            packet = {"question": "Review assigned prose", "writing_review": True}
            with patch.object(guidance, "canonical_writing_skill", return_value=entry):
                request = session.request("reviewer", packet, schemas.REVIEW, "canonical-review")
            self.assertIn("Single maintained test standard.", request["instructions"])
            self.assertNotIn("# Writing Review", request["instructions"])
            self.assertNotIn("legacy-writing-core.md", request["instructions"])
            self.assertNotIn("MAF section selection:", request["instructions"])
            with patch.object(guidance, "canonical_writing_skill", return_value=None):
                request = session.request("reviewer", packet, schemas.REVIEW, "standalone-review")
            self.assertIn("# Writing Review", request["instructions"])
            self.assertIn("legacy-writing-core.md", request["instructions"])

    def test_actual_entry_is_loaded_once_without_old_stack_and_sections_survive(self):
        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "SKILL.md"
            entry.write_text(ENTRY, encoding="utf-8")
            for mode in guidance.MODES:
                for section in [*guidance.SECTIONS, "full_manuscript"]:
                    scope = {"mode": mode, "sections": [section]}
                    for role in ("writer", "reviewer", "coordinator", "literature", "simulation", "mechanism"):
                        with self.subTest(mode=mode, section=section, role=role), patch.object(
                                guidance, "canonical_writing_skill", return_value=entry):
                            loaded = guidance.load_role(role, scope)
                            self.assertEqual(loaded.count("Single maintained test standard."), 1)
                            self.assertIn(str(entry), loaded)
                            self.assertIn(f"Assigned writing mode: {mode}; sections: {section}", loaded)
                            self.assertNotIn("Assigned writing method source:", loaded)
                            self.assertNotIn("# Scientific Editor", loaded)
                            self.assertNotIn("# Writing Review", loaded)
                            self.assertNotIn("# Scientific objects and sentence continuity", loaded)
                            selected = list(guidance.SECTIONS) if section == "full_manuscript" else [section]
                            for name in guidance.SECTIONS:
                                self.assertEqual(f"MAF section selection: {name}." in loaded, name in selected)
            with patch.object(guidance, "canonical_writing_skill", return_value=entry):
                self.assertIn("Single maintained test standard.", guidance.load_role("writer"))
                self.assertNotIn("Single maintained test standard.", guidance.load_role("literature"))

    def test_scope_contract_validation_and_nonwriting_jobs_are_unchanged(self):
        before = copy.deepcopy(schemas.CONTRACT)
        with patch.object(guidance, "canonical_writing_skill", side_effect=AssertionError("Should not resolve")):
            self.assertIn("# Research Coordinator", guidance.load_role("coordinator"))
        self.assertEqual(schemas.CONTRACT, before)
        with self.assertRaisesRegex(ValueError, "full_manuscript already selects all sections"):
            guidance.load_role("writer", {"mode": "revise", "sections": ["full_manuscript", "introduction"]})

    def test_canonical_scope_reaches_worker_review_and_coordinator_in_real_workflow(self):
        class ScopedDemo(DemoProvider):
            def __init__(self):
                super().__init__()
                self.requests = []

            async def ask(self, request):
                self.requests.append(copy.deepcopy(request))
                response = await super().ask(request)
                if request["request_id"].startswith("plan:"):
                    for task in response["tasks"]:
                        if task["role"] == "writer":
                            task["writing"] = {"mode": "revise", "sections": ["introduction"]}
                return response

        with tempfile.TemporaryDirectory() as directory:
            entry = Path(directory) / "SKILL.md"
            entry.write_text(ENTRY, encoding="utf-8")
            provider = ScopedDemo()
            workspace = Path(directory) / "project"
            with patch.object(guidance, "canonical_writing_skill", return_value=entry):
                result = asyncio.run(run_project(workspace, provider, brief="Scoped canonical writing", parallel=2))
            self.assertEqual(result["status"], "complete")
            for request_id in ("worker:T-write:1", "review:T-write:1", "decide:T-write:1"):
                request = next(item for item in provider.requests if item["request_id"] == request_id)
                self.assertIn("Single maintained test standard.", request["instructions"])
                self.assertIn("MAF section selection: introduction.", request["instructions"])
                self.assertNotIn("Assigned writing method source:", request["instructions"])
            self.assertTrue(state.audit(workspace)["protocol_ok"])
            self.assertEqual(json.loads(next(item for item in provider.requests
                                            if item["request_id"] == "worker:T-write:1")["prompt"])
                             ["task"]["writing"], {"mode": "revise", "sections": ["introduction"]})


if __name__ == "__main__":
    unittest.main()
