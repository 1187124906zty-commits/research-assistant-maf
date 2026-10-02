"""Progress governance checks without inspecting internal reasoning."""
import json
import unittest

from research_assistant.progress import (checked_decision, default_decision,
                                        diagnostic_question, parse_reports)


class ProgressTests(unittest.TestCase):
    def report(self, **changes):
        return {"checkpoint": 1, "activity": "repeated_polish", "current_work": "wording",
                "why_not_returned": "Trying another wording", "candidate": "results/report.md",
                "what_changed": "Wording only; no data or claim changed", "remaining_evidence": [],
                "new_evidence": False, "repetition_evidence": ["results/report.md revisions 2 and 3"], **changes}

    def tagged(self, value):
        return "<research-progress>" + json.dumps(value) + "</research-progress>"

    def test_tagged_public_report_parsed_but_plain_prose_ignored(self):
        report = self.report()
        self.assertEqual(parse_reports(self.tagged(report)), [report])
        self.assertEqual(parse_reports(json.dumps(report)), [])

    def test_malformed_or_unbounded_reports_ignored(self):
        for text in ("<research-progress>bad</research-progress>",
                     self.tagged([]), self.tagged(self.report(new_evidence="false")),
                     self.tagged(self.report(candidate="x" * 2001)),
                     self.tagged(self.report(checkpoint=True))):
            with self.subTest(text=text[:80]):
                self.assertEqual(parse_reports(text), [])

    def test_two_consistent_evidenced_reports_request_reviewable_candidate(self):
        decision = default_decision([self.report(), self.report(checkpoint=2)])
        self.assertEqual(decision["action"], "request_best_candidate")
        self.assertEqual(decision["evidence_origin"], "worker_reports_not_independently_verified")

    def test_single_report_elapsed_or_slow_activity_never_establishes_repetition(self):
        self.assertEqual(default_decision([self.report()])["action"], "continue")
        for activity in ("slow_work", "source_work", "unknown"):
            with self.subTest(activity=activity):
                reports = [self.report(activity=activity), self.report(checkpoint=2, activity=activity)]
                self.assertEqual(default_decision(reports)["action"], "continue")

    def test_new_candidate_or_new_evidence_keeps_work_running(self):
        for changes in ({"candidate": "new-report.md"}, {"new_evidence": True},
                        {"repetition_evidence": []}, {"repetition_evidence": [" "]},
                        {"what_changed": ""}, {"checkpoint": 1}):
            with self.subTest(changes=changes):
                second = self.report(**{"checkpoint": 2, **changes})
                self.assertEqual(default_decision([self.report(), second])["action"], "continue")

    def test_callback_cannot_ask_timer_only_handoff_or_interrupt(self):
        for decision in ({"action": "interrupt", "reason": "time", "evidence": ["time"]},
                         {"action": "request_best_candidate", "reason": "time", "evidence": []}):
            with self.subTest(decision=decision), self.assertRaises(ValueError):
                checked_decision(decision)

    def test_diagnostic_requests_public_rationale_and_original_final_schema(self):
        question = diagnostic_question(3)
        self.assertIn('"checkpoint":3', question)
        self.assertIn("Do not disclose private", question)
        self.assertIn("final answer in the original", question)


if __name__ == "__main__":
    unittest.main()
