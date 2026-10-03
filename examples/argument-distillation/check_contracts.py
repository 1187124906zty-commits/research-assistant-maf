"""Semantic regression fixtures, not a prose parser or writing quality score.

Run from a checkout with Python alone. Propositions are explicitly annotated
by a reviewer; no keywords are extracted from the accompanying sentence.
The numerical inputs are constructed counterexamples, not published results.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
from statistics import mean


def assess_claim(evidence: dict, proposition: dict) -> list[str]:
    """Check a small, explicit claim contract for this evaluation case only."""
    defects = []
    if proposition["kind"] == "performance":
        errors = evidence["errors"]
        if not errors or any(not math.isfinite(x) or x < 0 for x in errors):
            raise ValueError("Finite nonnegative candidate errors required")
        aggregate = {"minimum": min, "mean": mean}[proposition["aggregation"]]
        actual = aggregate(errors)
        if not math.isclose(actual, proposition["value"], rel_tol=1e-10, abs_tol=1e-12):
            defects.append("Reported value does not match the stated aggregation")
        if proposition["candidate_count"] != len(errors):
            defects.append("Candidate selection budget is misreported")
        if proposition["verified_population"] == "all" and set(evidence["verified_indices"]) != set(range(len(errors))):
            defects.append("Selected forward checks do not verify all candidates")
    elif proposition["kind"] == "uniqueness":
        # unique=False means the writer makes no uniqueness claim. Accepting
        # that restraint does not prove non-uniqueness of the complete space.
        matching = [candidate for candidate in evidence["candidates"]
                    if candidate["error"] <= evidence["matching_tolerance"]]
        if proposition["unique"] and len({tuple(c["parameters"]) for c in matching}) > 1:
            defects.append("Distinct matching parameter sets contradict uniqueness")
        elif proposition["unique"]:
            defects.append("Finite candidate screening cannot establish uniqueness")
    elif proposition["kind"] == "constraint":
        available = (set(evidence["enforced_quantities"]) if proposition["status"] == "enforced"
                     else set(evidence["evaluated_quantities"]))
        if not set(proposition["quantities"]).issubset(available):
            defects.append("Constraint or assessment scope exceeds the actual operation")
    elif proposition["kind"] == "independent_check":
        if proposition["independent"] and set(evidence["fit_data"]) & set(evidence["check_data"]):
            defects.append("Calibration data overlap the claimed independent check")
    elif proposition["kind"] == "compression":
        # These fields are semantic annotations supplied by a reviewer, not
        # tokens expected in the prose. Evidence includes a resolved exception
        # so a real scientific update is distinguishable from editorial loss.
        for field in evidence["required_distinctions"]:
            if field not in proposition["retained_distinctions"] and field not in evidence["resolved_distinctions"]:
                defects.append(f"Compression loses unresolved scientific distinction: {field}")
    elif proposition["kind"] == "source_count":
        actual = sum(evidence["constituent_counts"])
        if proposition["total"] != actual:
            defects.append("Source's reported total conflicts with its constituent counts")
    else:
        raise ValueError(f"Unsupported fixture claim: {proposition['kind']}")
    return defects


def cases() -> list[dict]:
    return [
        {"id": "best_is_not_mean", "evidence": {"errors": [0.02, 0.18, 0.30], "verified_indices": [0]},
         "positive": {"kind": "performance", "aggregation": "minimum", "value": 0.02, "candidate_count": 3, "verified_population": "selected"},
         "negative": {"kind": "performance", "aggregation": "mean", "value": 0.02, "candidate_count": 3, "verified_population": "selected"},
         "reversal": {"errors": [0.02, 0.02, 0.02], "verified_indices": [0]},
         "reason": "Same reported number becomes a valid mean only when actual candidate data justify it."},
        {"id": "selected_is_not_population", "evidence": {"errors": [0.02, 0.18, 0.30], "verified_indices": [0]},
         "positive": {"kind": "performance", "aggregation": "minimum", "value": 0.02, "candidate_count": 3, "verified_population": "selected"},
         "negative": {"kind": "performance", "aggregation": "minimum", "value": 0.02, "candidate_count": 3, "verified_population": "all"},
         "reversal": {"errors": [0.02, 0.18, 0.30], "verified_indices": [0, 1, 2]},
         "reason": "Universal verification changes support only after every generated candidate is actually checked."},
        {"id": "selection_is_not_uniqueness", "evidence": {"matching_tolerance": 0.03, "candidates": [{"parameters": [1, 2], "error": 0.01}, {"parameters": [2, 1], "error": 0.02}]},
         "positive": {"kind": "uniqueness", "unique": False},
         "negative": {"kind": "uniqueness", "unique": True},
         "reversal": None,
         "reason": "unique=False withholds a uniqueness claim; it is not a proof of full-space non-uniqueness. Finite candidate screening cannot establish uniqueness; two distinct matching designs can contradict it."},
        {"id": "global_projection_is_not_local_dynamics", "evidence": {"enforced_quantities": ["mean_composition"], "evaluated_quantities": []},
         "positive": {"kind": "constraint", "status": "enforced", "quantities": ["mean_composition"]},
         "negative": {"kind": "constraint", "status": "enforced", "quantities": ["mean_composition", "local_equilibrium"]},
         "reversal": {"enforced_quantities": ["mean_composition", "local_equilibrium"], "evaluated_quantities": []},
         "reason": "A stronger operational statement requires the additional operation, not stronger language."},
        {"id": "planned_is_not_evaluated", "evidence": {"enforced_quantities": ["weight"], "evaluated_quantities": []},
         "positive": {"kind": "constraint", "status": "enforced", "quantities": ["weight"]},
         "negative": {"kind": "constraint", "status": "evaluated", "quantities": ["manufacturability"]},
         "reversal": {"enforced_quantities": ["weight"], "evaluated_quantities": ["manufacturability"]},
         "reason": "Design feasibility and performed manufacturing assessment have separate evidence roles."},
        {"id": "calibration_is_not_independent", "evidence": {"fit_data": ["specimen-1"], "check_data": ["specimen-1"]},
         "positive": {"kind": "independent_check", "independent": False},
         "negative": {"kind": "independent_check", "independent": True},
         "reversal": {"fit_data": ["specimen-1"], "check_data": ["specimen-2"]},
         "reason": "The sentence gains independent-check support only when the actual data roles change."},
        {"id": "concise_is_not_unconditional", "evidence": {"required_distinctions": ["tested_range", "candidate_cause", "alternative_explanation"], "resolved_distinctions": []},
         "positive": {"kind": "compression", "retained_distinctions": ["tested_range", "candidate_cause", "alternative_explanation"]},
         "negative": {"kind": "compression", "retained_distinctions": ["tested_range", "candidate_cause"]},
         "reversal": {"required_distinctions": ["tested_range", "candidate_cause", "alternative_explanation"], "resolved_distinctions": ["alternative_explanation"]},
         "reason": "An alternative can disappear after discriminating evidence resolves it, not merely to shorten prose."},
        {"id": "authors_summary_is_not_automatic_support", "evidence": {"constituent_counts": [24, 16], "authors_reported_total": 42},
         "positive": {"kind": "source_count", "total": 40},
         "negative": {"kind": "source_count", "total": 42},
         "reversal": {"constituent_counts": [26, 16], "authors_reported_total": 42},
         "reason": "Constructed source contradiction: citing the author does not repair inconsistent arithmetic; investigate the denominator/version."},
    ]


def run() -> dict:
    results = []
    for case in cases():
        positive = assess_claim(case["evidence"], case["positive"])
        negative = assess_claim(case["evidence"], case["negative"])
        reversal = (assess_claim(case["reversal"], case["negative"])
                    if case["reversal"] is not None else None)
        if positive or not negative or reversal:
            raise AssertionError(f"Failed semantic regression: {case['id']}")
        results.append({"id": case["id"], "negative_defects": negative,
                        "counterevidence_reverses_judgment": reversal == [],
                        "reason": case["reason"]})
    return {"status": "passed", "case_count": len(results), "results": results,
            "scope": "Hand-annotated semantic contracts on constructed evidence; no prose parsing, model execution or general writing-quality claim."}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = json.dumps(run(), ensure_ascii=False, indent=2) + "\n"
    if args.output:
        with args.output.open("x", encoding="utf-8") as stream:
            stream.write(report)
    print(report)
