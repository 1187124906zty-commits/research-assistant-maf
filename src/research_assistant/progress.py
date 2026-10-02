"""Public progress reports and conservative decisions, not hidden reasoning.

Elapsed time initiates a question. It is never evidence that work is futile.
Reports are worker statements; an external review still judges their science.
"""
from __future__ import annotations

import json
import re
from typing import Any

MARKER = "research-progress"
ACTIVITIES = {"slow_work", "source_work", "repeated_polish", "unknown"}


def diagnostic_question(checkpoint: int) -> str:
    return (
        f"Progress checkpoint {checkpoint}: the elapsed interval is a request for status, "
        "not a stop instruction. Continue useful work. In a short public commentary "
        "message, describe what you are doing, why the task has not returned, the "
        "best current candidate/artifact, what changed since the previous checkpoint "
        "and what evidence is still needed. Distinguish slow thought or source work "
        "from repeated polishing without new evidence. Do not disclose private "
        "chain-of-thought; report observable work and a concise rationale. "
        "Use this tagged JSON in commentary (keep the final answer in the original "
        "output schema): <research-progress>{"
        f'"checkpoint":{checkpoint},'
        '"activity":"slow_work|source_work|repeated_polish|unknown",'
        '"current_work":"...","why_not_returned":"...","candidate":"...",'
        '"what_changed":"...","remaining_evidence":["..."],'
        '"new_evidence":true,"repetition_evidence":["artifact/tool reference and observed repetition"]'
        "}</research-progress>. If uncertain, say unknown; do not fabricate evidence."
    )


def best_candidate_question(reason: str) -> str:
    return (
        "Coordination feedback after your progress report: " + reason + "\n"
        "Return the best current candidate and its actual artifacts in the original "
        "output schema so a separate reviewer can assess it. Preserve unresolved "
        "evidence, limitations and negative findings. Separate essential missing "
        "validation from optional polish; do not claim unsupported completion. "
        "This is a reasoned handoff request, not a timer-based interruption."
    )


def parse_reports(text: str) -> list[dict[str, Any]]:
    """Accept bounded tagged public reports; ignore prose and reasoning events."""
    reports = []
    for raw in re.findall(r"<research-progress>(.*?)</research-progress>", text, re.S):
        if len(raw) > 12000:
            continue
        try:
            value = json.loads(raw)
        except (TypeError, ValueError):
            continue
        if not isinstance(value, dict) or type(value.get("checkpoint")) is not int:
            continue
        if value["checkpoint"] < 1 or value.get("activity") not in ACTIVITIES:
            continue
        if type(value.get("new_evidence")) is not bool:
            continue
        fields = ("current_work", "why_not_returned", "candidate", "what_changed")
        if not all(isinstance(value.get(k), str) and len(value[k]) <= 2000 for k in fields):
            continue
        lists = ("remaining_evidence", "repetition_evidence")
        if not all(isinstance(value.get(k), list) and len(value[k]) <= 10 and
                   all(isinstance(v, str) and len(v) <= 2000 for v in value[k]) for k in lists):
            continue
        reports.append({key: value[key] for key in ("checkpoint", "activity", *fields,
                                                    *lists, "new_evidence")})
    return reports


def default_decision(reports: list[dict]) -> dict:
    """Require two consistent, reference-bearing returns before proposing handoff.

    This evidence is explicitly self-reported. The proposal requests a reviewable
    candidate, never scientific acceptance or cancellation of the active turn.
    """
    last = reports[-1]
    repeated = len(reports) >= 2 and all(
        value["activity"] == "repeated_polish" and not value["new_evidence"]
        and bool(value["repetition_evidence"]) and all(ref.strip() for ref in value["repetition_evidence"])
        and bool(value["what_changed"].strip())
        and bool(value["candidate"].strip()) for value in reports[-2:])
    if repeated:
        previous = reports[-2]
        repeated = previous["checkpoint"] != last["checkpoint"] and previous["candidate"] == last["candidate"]
    if repeated:
        return {"action": "request_best_candidate", "reason":
                "Two public progress reports describe repeated polish of the same candidate "
                "without new evidence and cite concrete work references; request independent "
                "review of that candidate, retaining all missing validation.",
                "evidence": [item for value in reports[-2:] for item in value["repetition_evidence"]],
                "evidence_origin": "worker_reports_not_independently_verified"}
    return {"action": "continue", "reason":
            "Slow/source/unknown work or insufficient repetition evidence; elapsed time alone does not justify stopping.",
            "evidence": []}


def checked_decision(value: Any) -> dict | None:
    """A callback can request handoff only with a reason and observable evidence."""
    if value is None:
        return None
    if not isinstance(value, dict) or value.get("action") not in {"continue", "request_best_candidate"}:
        raise ValueError("Progress decision must continue or request_best_candidate")
    if not isinstance(value.get("reason"), str) or not value["reason"].strip():
        raise ValueError("Progress decision requires a reason")
    evidence = value.get("evidence", [])
    if not isinstance(evidence, list) or not all(isinstance(v, str) and v.strip() for v in evidence):
        raise ValueError("Progress decision evidence must be concrete text references")
    if value["action"] == "request_best_candidate" and not evidence:
        raise ValueError("Best-candidate handoff requires evidence, not elapsed time")
    return {**value, "evidence": evidence}
