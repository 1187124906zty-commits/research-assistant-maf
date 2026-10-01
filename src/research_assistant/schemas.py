"""Explicit model output contracts; domain state performs semantic checks."""


def obj(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def array(items):
    return {"type": "array", "items": items}


TEXT = {"type": "string"}
BOOL = {"type": "boolean"}
INTEGER = {"type": "integer"}
STRINGS = array(TEXT)
ROLES = ["literature", "simulation", "mechanism", "writer"]
LOCATOR = obj({"path": TEXT})
CLAIM = obj({"id": TEXT, "statement": TEXT})
DEPENDENCY = obj({"task_id": TEXT, "claim_ids": STRINGS,
                  "affects_claim_ids": STRINGS,
                  "required_level": {"type": ["string", "null"], "enum": [
                      "observation", "numerical_verification", "physical_validation", None]}})
CONTRACT = obj({"id": TEXT, "role": {"type": "string", "enum": ROLES},
                "question": TEXT, "purpose": TEXT, "claim_ids": STRINGS,
                "inputs": array(LOCATOR), "outputs": STRINGS, "writes": STRINGS,
                "acceptance": STRINGS,
                "budget": obj({"max_attempts": INTEGER, "max_no_progress": INTEGER}),
                "depends_on": array(DEPENDENCY)})
PLAN_UPDATE = obj({"reason": TEXT, "facts": STRINGS, "hypotheses": STRINGS,
                   "uncertainties": STRINGS, "next_decision": TEXT,
                   "claims": array(CLAIM)})
PLAN = obj({"action": {"type": "string", "enum": ["work", "complete", "needs_input"]},
            "reason": TEXT, "plan": PLAN_UPDATE, "tasks": array(CONTRACT),
            "deliverables": STRINGS})
EVIDENCE = obj({"path": TEXT, "level": {"type": "string", "enum": [
    "observation", "numerical_verification", "physical_validation"]},
    "kind": {"type": "string", "enum": ["observation", "support", "negative", "counterevidence"]},
    "claim_ids": STRINGS, "summary": TEXT})
BLOCKER = obj({"claim_ids": STRINGS, "reason": TEXT, "kind": TEXT})
CONTRIBUTION = obj({"answer": TEXT, "effect_on_project": TEXT,
                    "uncertainties": STRINGS, "next_options": STRINGS,
                    "cost_note": TEXT})
RESULT = obj({"attempt": INTEGER, "changed_understanding": BOOL, "reason": TEXT,
              "evidence": array(EVIDENCE), "blockers": array(BLOCKER),
              "contribution": CONTRIBUTION})
FINDING = obj({"blocking": BOOL, "claim_ids": STRINGS, "reason": TEXT,
               "evidence_paths": STRINGS})
REVIEW = obj({"summary": TEXT, "findings": array(FINDING), "limitations": STRINGS})
PROMOTION = obj({"claim_id": TEXT, "level": {"type": "string", "enum": [
    "observation", "numerical_verification", "physical_validation"]},
    "evidence_indices": array(INTEGER), "reason": TEXT})
RESOLUTION = obj({"claim_id": TEXT, "challenge_id": TEXT,
                  "evidence_indices": array(INTEGER), "reason": TEXT})
CLAIM_UPDATE = obj({"claim_id": TEXT, "status": {"type": "string", "enum": [
    "narrowed", "parked", "invalidated"]}, "reason": TEXT})
REASSESSMENT = obj({"reason": TEXT, "strategy_change": TEXT, "additional_attempts": INTEGER})
DECISION = obj({"action": {"type": "string", "enum": ["accept", "continue", "narrow", "reframe", "park"]},
                "reason": TEXT, "promotions": array(PROMOTION),
                "resolutions": array(RESOLUTION), "claim_updates": array(CLAIM_UPDATE),
                "reassessment": {"anyOf": [REASSESSMENT, {"type": "null"}]}})
