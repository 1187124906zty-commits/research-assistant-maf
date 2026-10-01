"""Deterministic protocol demonstration, not empirical AI/science evaluation."""
from __future__ import annotations

import json
from pathlib import Path


class DemoProvider:
    def __init__(self):
        self.calls = []

    async def ask(self, request):
        self.calls.append(request["request_id"])
        packet = json.loads(request["prompt"])
        root = Path(request["cwd"])
        role = request["role"]
        if role == "coordinator" and request["request_id"].startswith("plan:"):
            tasks = packet["tasks"]
            plan = {"reason": "Demonstrate scoped evidence, negative return and a readable deliverable",
                    "facts": [], "hypotheses": [], "uncertainties": ["No physical validation in this protocol demo"],
                    "next_decision": "Interpret actual artifact roles", "claims": []}
            if not tasks:
                plan["claims"] = [{"id": "C1", "statement": "The specified controlled observation supports the original candidate"}]
                contracts = [self.contract("T-evidence", "simulation", ["C1"], "results/T-evidence"),
                             self.contract("T-background", "literature", [], "results/T-background")]
                return {"action": "work", "reason": "Produce two independent bounded artifacts", "plan": plan,
                        "tasks": contracts[:packet["max_ready_tasks"]], "deliverables": []}
            if "T-write" not in tasks:
                contract = self.contract("T-write", "writer", [], "manuscript")
                contract["inputs"] = [{"path": "results/T-evidence/observation.json"}]
                return {"action": "work", "reason": "Write the bounded interpretation including the negative finding",
                        "plan": plan, "tasks": [contract], "deliverables": []}
            return {"action": "complete", "reason": "Protocol demo has a real scoped document; no research efficacy claim",
                    "plan": plan, "tasks": [], "deliverables": ["manuscript/report.md"]}
        if role == "coordinator":
            tid = packet["handoff"]["task"]["id"]
            updates = [{"claim_id": "C1", "status": "parked", "reason": "Negative return does not support this candidate"}] if tid == "T-evidence" else []
            return {"action": "accept", "reason": "Useful truthful return accepted, not an automatic hypothesis promotion",
                    "promotions": [], "resolutions": [], "claim_updates": updates, "reassessment": None}
        if role == "reviewer":
            for artifact in packet["evidence"]:
                if not (root / artifact["path"]).is_file():
                    raise RuntimeError("Demo reviewer could not find actual evidence")
            return {"summary": "Artifacts exist and preserve the declared protocol-demo limits",
                    "findings": [], "limitations": ["Deterministic fixture, not independent LLM behavior evaluation"]}
        tid = packet["task"]["id"]
        if role == "simulation":
            path = root / "results/T-evidence/observation.json"
            content = {"fixture": "protocol-only", "observed": "candidate unsupported", "physical_validation": False}
            kind, cids = "negative", ["C1"]
        elif role == "literature":
            path = root / "results/T-background/notes.json"
            content = {"fixture": "protocol-only", "note": "A local demonstration; no fabricated literature references"}
            kind, cids = "observation", []
        else:
            path = root / "manuscript/report.md"
            content = "# Bounded protocol demonstration\n\nThe candidate returned a negative observation. The task was accepted as useful delivery; the claim remains unpromoted. No physical validation or scientific discovery is asserted.\n"
            kind, cids = "observation", []
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content if isinstance(content, str) else json.dumps(content, indent=2), encoding="utf-8")
        return {"attempt": packet["next_attempt"], "changed_understanding": True,
                "reason": "The requested artifact makes the next disposition explicit",
                "evidence": [{"path": str(path.relative_to(root)), "level": "observation", "kind": kind,
                              "claim_ids": cids, "summary": "Actual local fixture artifact"}], "blockers": [],
                "contribution": {"answer": "Bounded question answered", "effect_on_project": "Supports truthful handoff and scoped writing",
                                 "uncertainties": ["Fixture cannot establish scientific validity"], "next_options": ["Write limits explicitly"],
                                 "cost_note": "No model or solver was called"}}

    @staticmethod
    def contract(tid, role, claims, output):
        return {"id": tid, "role": role, "question": "Answer the specified protocol demonstration question",
                "purpose": "Demonstrate real artifacts and correct handoff semantics", "claim_ids": claims,
                "inputs": [], "outputs": [output], "writes": [output],
                "acceptance": ["Actual artifact with explicit scope and honest evidence category"],
                "budget": {"max_attempts": 1, "max_no_progress": 1}, "depends_on": []}
