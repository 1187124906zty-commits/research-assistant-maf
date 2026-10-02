"""Derived from ResearchFlow (MIT, 2026 ResearchFlow contributors).

Persistent research memory and deterministic handoff checks.

Only the coordinator invokes mutations. Workers write results in their declared
workspace, then return a JSON report for coordinator import. ``actor`` is a
protocol identity, not an operating-system security boundary. Evidence hashes
bind claims to a particular artifact revision, not to its scientific quality.
"""

from __future__ import annotations

import copy
import hashlib
import json
import os
import re
import tempfile
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .guidance import writing_selection


LEVELS = {"observation", "numerical_verification", "physical_validation"}
KINDS = {"observation", "support", "negative", "counterevidence"}
CLOSED = {"accepted", "narrowed", "reframed", "parked"}
ACTIONS = {"accept": "accepted", "continue": "active", "narrow": "narrowed", "reframe": "reframed", "park": "parked"}
SAFE_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,99}$")


class GovernanceError(ValueError):
    """A concrete protocol requirement was not met."""


def _require(condition: bool, message: str) -> None:
    if not condition:
        raise GovernanceError(message)


def _text(value: Any, name: str) -> str:
    _require(isinstance(value, str) and bool(value.strip()), f"{name} must be a nonempty string")
    return value


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _paths(project: str | Path) -> tuple[Path, Path]:
    root = Path(project).resolve()
    return root, root / ".research-assistant"


def _load(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, json.JSONDecodeError) as exc:
        raise GovernanceError(f"Cannot read {path}: {exc}") from exc


def _atomic(path: Path, value: Any) -> None:
    fd, name = tempfile.mkstemp(prefix=".writing-", dir=path.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
            json.dump(value, stream, ensure_ascii=False, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def _events(directory: Path, repair_tail: bool = False) -> list[dict]:
    path = directory / "events.jsonl"
    if not path.exists():
        return []
    raw = path.read_bytes()
    if raw and not raw.endswith(b"\n"):
        if not repair_tail:
            raise GovernanceError("Journal has an incomplete last line; run a coordinator command to recover")
        raw = raw[: raw.rfind(b"\n") + 1]
        with path.open("wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    try:
        return [json.loads(line) for line in raw.decode("utf-8").splitlines() if line]
    except (ValueError, UnicodeError) as exc:
        raise GovernanceError("Journal contains a damaged complete event; preserve files and investigate") from exc


def _append(directory: Path, event: dict) -> None:
    with (directory / "events.jsonl").open("a", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(event, ensure_ascii=False) + "\n")
        stream.flush()
        os.fsync(stream.fileno())


def _recover(directory: Path) -> None:
    pending = directory / "transaction.json"
    entries = _events(directory, repair_tail=True)
    if not pending.exists():
        return
    tx = _load(pending)
    event, state = tx["event"], tx["state"]
    current_path = directory / "research-state.json"
    current = _load(current_path) if current_path.exists() else {"revision": 0}
    _require(current["revision"] <= state["revision"], "Recovery state is older than current state")
    if current["revision"] < state["revision"]:
        _atomic(current_path, state)
    matching = [entry for entry in entries if entry["seq"] == event["seq"]]
    _require(not matching or matching == [event], "Recovery journal conflicts with pending transaction")
    if not matching:
        _require(not entries or entries[-1]["seq"] == event["seq"] - 1, "Recovery journal sequence is inconsistent")
        _append(directory, event)
    pending.unlink()


@contextmanager
def _locked(directory: Path):
    directory.mkdir(parents=True, exist_ok=True)
    lock = directory / "writer.lock"
    stream = lock.open("a+b")
    if stream.seek(0, os.SEEK_END) == 0:
        stream.write(b"0")
        stream.flush()
    stream.seek(0)
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
    except OSError as exc:
        stream.close()
        raise GovernanceError("Another coordinator writer holds the project lock") from exc
    try:
        _recover(directory)
        yield
    finally:
        stream.seek(0)
        if os.name == "nt":
            msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
        else:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def _read(project: str | Path) -> tuple[Path, Path, dict]:
    root, directory = _paths(project)
    state = _load(directory / "research-state.json")
    _require(state.get("schema_version") == 1, "Unsupported research state version")
    return root, directory, state


def _actor(state: dict, actor: str | None) -> None:
    _require(actor is None or actor == state["project"]["coordinator"], "Only the declared coordinator imports results and updates shared state")


def _commit(directory: Path, state: dict, kind: str, payload: dict) -> dict:
    state["revision"] += 1
    state["updated"] = _now()
    event = {"seq": state["revision"], "time": state["updated"], "kind": kind, "payload": payload}
    pending = directory / "transaction.json"
    _atomic(pending, {"event": event, "state": state})
    _atomic(directory / "research-state.json", state)
    _append(directory, event)
    pending.unlink()
    return state


def _resolve(root: Path, path: str) -> Path:
    _text(path, "locator.path")
    return (root / path).resolve()


def _revision(path: Path) -> str:
    _require(path.is_file(), f"Evidence/input file does not exist: {path}")
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return "sha256:" + digest.hexdigest()


def _locator(root: Path, value: dict, require_fresh: bool = False) -> dict:
    _require(isinstance(value, dict), "A locator must be an object containing path")
    item = copy.deepcopy(value)
    actual = _revision(_resolve(root, item.get("path")))
    item.setdefault("revision", actual)
    _text(item["revision"], "locator.revision")
    if require_fresh:
        _require(item["revision"] == actual, f"Stale input revision: {item['path']}")
    return item


def _fresh(root: Path, locator: dict) -> bool:
    try:
        return _revision(_resolve(root, locator["path"])) == locator["revision"]
    except GovernanceError:
        return False


def snapshot(project: str | Path, paths: list[str]) -> list[dict]:
    """Bind existing files to revisions without hand-copying hashes."""
    root, _ = _paths(project)
    return [_locator(root, {"path": path}) for path in paths]


def _apply_plan(state: dict, update: dict) -> None:
    _require(isinstance(update, dict), "Plan must be an object")
    allowed = {"question", "purpose", "target_journal", "stage", "constraints", "facts", "hypotheses", "uncertainties", "next_decision", "claims", "reason"}
    _require(not set(update) - allowed, f"Unknown plan fields: {sorted(set(update) - allowed)}")
    for key in ("question", "purpose", "target_journal", "stage", "constraints"):
        if key in update:
            if key == "constraints":
                _require(isinstance(update[key], list), "constraints must be a list")
            else:
                _text(update[key], key)
            state["project"][key] = copy.deepcopy(update[key])
    for key in ("facts", "hypotheses", "uncertainties", "next_decision"):
        if key in update:
            _require(isinstance(update[key], list) if key != "next_decision" else isinstance(update[key], (str, dict)), f"Invalid {key}")
            state["research"][key] = copy.deepcopy(update[key])
    _require(isinstance(update.get("claims", []), list), "claims must be a list")
    for value in update.get("claims", []):
        cid = _text(value.get("id"), "claim.id")
        _require(SAFE_ID.fullmatch(cid) is not None, "Invalid claim id")
        _require(cid not in state["claims"], f"Claim {cid} exists; create a new id for a changed assertion and use disposition to retire the old claim")
        state["claims"][cid] = {"id": cid, "statement": _text(value.get("statement"), "claim.statement"), "status": "hypothesis", "support": {}, "challenges": [], "limitations": []}


def initialize(project: str | Path, question: str, config: dict | None = None, coordinator: str = "coordinator") -> dict:
    root, directory = _paths(project)
    root.mkdir(parents=True, exist_ok=True)
    with _locked(directory):
        _require(not (directory / "research-state.json").exists(), "Project already initialized")
        state = {"schema_version": 1, "revision": 0, "created": _now(), "project": {"question": _text(question, "question"), "purpose": question, "stage": "exploration", "target_journal": None, "constraints": [], "coordinator": _text(coordinator, "coordinator")}, "research": {"facts": [], "hypotheses": [], "uncertainties": [], "next_decision": ""}, "claims": {}, "tasks": {}}
        if config:
            _apply_plan(state, config)
        return _commit(directory, state, "initialize", {"question": state["project"]["question"]})


def plan(project: str | Path, update: dict, actor: str | None = None) -> dict:
    """Replace the indicated research-memory fields; omitted fields survive."""
    _, directory = _paths(project)
    with _locked(directory):
        _, _, state = _read(project)
        _actor(state, actor)
        _text(update.get("reason"), "plan.reason")
        _apply_plan(state, update)
        return _commit(directory, state, "plan", {"reason": update["reason"], "fields": sorted(update)})


def _write_paths(root: Path, values: list[str]) -> list[Path]:
    _require(isinstance(values, list) and bool(values), "writes/outputs must be a nonempty list of project-relative paths")
    paths = [_resolve(root, value) for value in values]
    for path in paths:
        _require(path.is_relative_to(root) and path != root and not path.is_relative_to(root / ".research-assistant"), "Workers may write only declared project paths outside .research-assistant")
    return paths


def _dependencies(contract: dict):
    for value in contract.get("depends_on", []):
        yield {"task_id": value} if isinstance(value, str) else value


def _dependency_issues(root: Path, state: dict, contract: dict, claim_id: str | None = None, seen: set | None = None) -> list[str]:
    issues = []
    for dep in _dependencies(contract):
        if claim_id is not None and claim_id not in dep.get("affects_claim_ids", contract["claim_ids"]):
            continue
        prerequisite = state["tasks"].get(dep["task_id"])
        if prerequisite is None or prerequisite["status"] not in CLOSED:
            issues.append(f"Dependency {dep['task_id']} lacks requester disposition")
        for cid in dep.get("claim_ids", []):
            claim = state["claims"][cid]
            if dep.get("required_level"):
                if not _claim_current(root, state, cid, dep["required_level"], seen):
                    issues.append(f"Dependency claim {cid} lacks current {dep['required_level']} support")
            elif claim["status"] in {"invalidated", "parked", "narrowed"}:
                issues.append(f"Dependency claim {cid} is {claim['status']}")
    return issues


def _claim_current(root: Path, state: dict, cid: str, level: str, seen: set | None = None) -> bool:
    """Check current artifact/dependency binding, never the scientific inference."""
    visited = set(seen or ())
    if (cid, level) in visited:
        return False
    visited.add((cid, level))
    claim = state["claims"][cid]
    evidence = claim["support"].get(level, [])
    if claim["status"] != "supported" or not evidence or any(not item["resolved"] for item in claim["challenges"]):
        return False
    for item in evidence:
        if item.get("level") != level or item.get("kind") != "support" or cid not in item.get("claim_ids", []) or not _fresh(root, item):
            return False
        source = state["tasks"].get(item.get("task_id"))
        if source is None or any(not _fresh(root, locator) for locator in source["contract"]["inputs"]):
            return False
        if _dependency_issues(root, state, source["contract"], cid, visited):
            return False
    return True


def _propagate_invalidations(state: dict, changed_claims: set[str], reason: str) -> None:
    """Invalidate only support that was produced using a named affected dependency."""
    affected = set(changed_claims)
    progress = True
    while progress:
        progress = False
        for tid, entry in state["tasks"].items():
            impacted = set()
            for dep in _dependencies(entry["contract"]):
                if set(dep.get("claim_ids", [])) & affected:
                    impacted.update(dep.get("affects_claim_ids", entry["contract"]["claim_ids"]))
            if impacted:
                entry["dependency_invalidations"] = {"claim_ids": sorted(impacted), "reason": reason}
            for cid in impacted:
                claim = state["claims"][cid]
                derived_here = any(item.get("task_id") == tid for items in claim["support"].values() for item in items)
                if claim["status"] == "supported" and derived_here:
                    claim["status"] = "invalidated"
                    claim["limitations"].append(f"Dependency invalidated: {reason}")
                    if cid not in affected:
                        affected.add(cid)
                        progress = True


def _prepare_task(root: Path, state: dict, contract: dict) -> dict:
    value = copy.deepcopy(contract)
    if "writing" in value:
        try:
            value["writing"] = writing_selection(value["writing"])
        except ValueError as exc:
            raise GovernanceError(str(exc)) from exc
        _require(value["writing"] is not None, "Omit task.writing rather than setting it null")
    tid = _text(value.get("id"), "task.id")
    _require(SAFE_ID.fullmatch(tid) is not None and tid not in state["tasks"], "Task id is invalid or already exists")
    for field in ("role", "question", "purpose"):
        _text(value.get(field), f"task.{field}")
    _require(isinstance(value.get("claim_ids"), list), "claim_ids must be a list (possibly empty)")
    _require(set(value["claim_ids"]) <= state["claims"].keys(), "Task refers to unknown claim ids")
    _require(bool(value.get("acceptance")), "Task needs claim-relative acceptance criteria")
    budget = value.get("budget", {})
    for field in ("max_attempts", "max_no_progress"):
        _require(type(budget.get(field)) is int and budget[field] > 0, f"budget.{field} must be a positive integer")
    _require(isinstance(value.get("inputs", []), list), "inputs must be a list")
    value["inputs"] = [_locator(root, item, require_fresh=True) for item in value.get("inputs", [])]
    value.setdefault("depends_on", [])
    _require(isinstance(value["depends_on"], list), "depends_on must be a list")
    for dep in _dependencies(value):
        prerequisite = state["tasks"].get(dep.get("task_id"))
        _require(prerequisite is not None and prerequisite["status"] in CLOSED, f"Dependency {dep.get('task_id')} lacks requester disposition")
        cids = dep.get("claim_ids", [])
        _require(set(cids) <= state["claims"].keys(), "Dependency has unknown claim ids")
        _require(set(dep.get("affects_claim_ids", value["claim_ids"])) <= set(value["claim_ids"]), "Dependency affects_claim_ids must lie in this task's scope")
        if dep.get("required_level"):
            _require(dep["required_level"] in LEVELS, "Unknown required_level")
            _require(bool(cids), "A required_level dependency must identify claim_ids")
            for cid in cids:
                _require(_claim_current(root, state, cid, dep["required_level"]), f"Dependency claim {cid} lacks current {dep['required_level']} support")
    _require(not _dependency_issues(root, state, value), "; ".join(_dependency_issues(root, state, value)))
    outputs = _write_paths(root, value.get("outputs"))
    value.setdefault("writes", value["outputs"])
    writes = _write_paths(root, value["writes"])
    _require(all(any(path == owner or path.is_relative_to(owner) for owner in writes) for path in outputs), "Every output must lie inside declared writes")
    for existing in state["tasks"].values():
        if existing["status"] not in CLOSED:
            owned = _write_paths(root, existing["contract"]["writes"])
            _require(not any(a == b or a.is_relative_to(b) or b.is_relative_to(a) for a in writes for b in owned), f"Active task write ownership overlaps {existing['contract']['id']}")
    value.setdefault("owner", value["role"])
    value["project_revision"] = state["revision"]
    state["tasks"][tid] = {"contract": value, "status": "active", "attempts": [], "decisions": [], "no_progress_count": 0, "attempt_limit": budget["max_attempts"], "reviewed_no_progress": 0}
    return state["tasks"][tid]


def task(project: str | Path, contract: dict, actor: str | None = None) -> dict:
    """Register one bounded task."""
    root, directory = _paths(project)
    with _locked(directory):
        _, _, state = _read(project)
        _actor(state, actor)
        entry = _prepare_task(root, state, contract)
        _commit(directory, state, "task", {"task_id": contract["id"], "claim_ids": contract["claim_ids"]})
        return entry


def dispatch_batch(project: str | Path, update: dict, contracts: list[dict], actor: str | None = None) -> dict:
    """Atomically validate/apply a ready batch and its research understanding."""
    root, directory = _paths(project)
    with _locked(directory):
        _, _, current = _read(project)
        _actor(current, actor)
        candidate = copy.deepcopy(current)
        _text(update.get("reason"), "plan.reason")
        _apply_plan(candidate, update)
        for contract in contracts:
            _prepare_task(root, candidate, contract)
        return _commit(directory, candidate, "dispatch_batch", {"reason": update["reason"], "tasks": [c["id"] for c in contracts]})


def record(project: str | Path, task_id: str, result: dict, actor: str | None = None) -> dict:
    """Import an honest positive, negative, or incomplete result; never promote claims."""
    root, directory = _paths(project)
    with _locked(directory):
        _, _, state = _read(project)
        _actor(state, actor)
        entry = state["tasks"].get(task_id)
        _require(entry is not None and entry["status"] == "active", "Task must be active to import its next result")
        _require(len(entry["attempts"]) < entry["attempt_limit"], "Attempt budget exhausted; coordinator must reassess before continuing")
        value = copy.deepcopy(result)
        _require(type(value.get("attempt")) is int and value["attempt"] == len(entry["attempts"]) + 1, "attempt must be the next consecutive integer")
        _require(type(value.get("changed_understanding")) is bool, "changed_understanding must be boolean")
        _text(value.get("reason"), "result.reason")
        _require(isinstance(value.get("evidence"), list), "evidence must be a list (empty for a documented failed attempt)")
        _require(isinstance(value.get("blockers"), list), "blockers must be a list")
        claims = entry["contract"]["claim_ids"]
        invalidated = set()
        evidence = []
        for index, item in enumerate(value["evidence"]):
            bound = _locator(root, item)
            _require(bound.get("level") in LEVELS, "Evidence level must be observation, numerical_verification, or physical_validation")
            _require(bound.get("kind") in KINDS, "Evidence kind must be observation, support, negative, or counterevidence")
            _require(isinstance(bound.get("claim_ids"), list) and set(bound["claim_ids"]) <= set(claims), "Evidence claim_ids must lie in this task's scope")
            _text(bound.get("summary"), "evidence.summary")
            evidence.append(bound)
            if bound["kind"] == "counterevidence":
                for cid in bound["claim_ids"]:
                    claim = state["claims"][cid]
                    claim["status"] = "invalidated"
                    invalidated.add(cid)
                    claim["challenges"].append({"id": f"{task_id}:{value['attempt']}:evidence:{index}", "task_id": task_id, "attempt": value["attempt"], "reason": bound["summary"], "level": bound["level"], "path": bound["path"], "revision": bound["revision"], "origin_evidence": [{"path": bound["path"], "revision": bound["revision"]}], "resolved": False})
        value["evidence"] = evidence
        for index, blocker in enumerate(value["blockers"]):
            _require(isinstance(blocker.get("claim_ids"), list) and bool(blocker["claim_ids"]) and set(blocker["claim_ids"]) <= set(claims), "Each blocker must name affected claims in task scope")
            _text(blocker.get("reason"), "blocker.reason")
            for cid in blocker["claim_ids"]:
                claim = state["claims"][cid]
                claim["challenges"].append({"id": f"{task_id}:{value['attempt']}:blocker:{index}", "task_id": task_id, "attempt": value["attempt"], "reason": blocker["reason"], "kind": blocker.get("kind", "unspecified"), "origin_evidence": [{"path": item["path"], "revision": item["revision"]} for item in evidence if cid in item["claim_ids"]], "resolved": False})
                if claim["status"] == "supported":
                    claim["status"] = "invalidated"
                    invalidated.add(cid)
        _propagate_invalidations(state, invalidated, f"New evidence/blocker returned by {task_id}, attempt {value['attempt']}")
        entry["attempts"].append(value)
        entry["no_progress_count"] = 0 if value["changed_understanding"] else entry["no_progress_count"] + 1
        if value["changed_understanding"]:
            entry["reviewed_no_progress"] = 0
        entry["status"] = "awaiting_decision"
        _commit(directory, state, "record", {"task_id": task_id, "attempt": value["attempt"], "changed_understanding": value["changed_understanding"]})
        return value


def _selected_evidence(root: Path, entry: dict, indices: list, cid: str, level: str | None = None) -> list[dict]:
    _require(isinstance(indices, list) and bool(indices) and all(type(i) is int for i in indices), "Specific evidence_indices are required")
    evidence = entry["attempts"][-1]["evidence"]
    _require(all(0 <= i < len(evidence) for i in indices), "Evidence index out of range")
    selected = [evidence[i] for i in indices]
    _require(all(cid in item["claim_ids"] for item in selected), "Evidence does not address this claim")
    _require(all(_fresh(root, item) for item in selected), "Selected evidence is missing or stale")
    if level:
        _require(all(item["level"] == level and item["kind"] == "support" for item in selected), "Promotion requires explicit supporting evidence at the exact requested validation level")
    return selected


def decide(project: str | Path, task_id: str, decision: dict, actor: str | None = None) -> dict:
    """Requester disposition and reasoned reassessment, separate from scientific support."""
    root, directory = _paths(project)
    with _locked(directory):
        _, _, state = _read(project)
        _actor(state, actor)
        entry = state["tasks"].get(task_id)
        _require(entry is not None and entry["status"] == "awaiting_decision", "Task needs a new result before disposition")
        value = copy.deepcopy(decision)
        action = value.get("action")
        _require(action in ACTIONS, "Unknown disposition action")
        _text(value.get("reason"), "decision.reason")
        if action == "continue":
            spent = len(entry["attempts"]) >= entry["attempt_limit"]
            stalled = entry["no_progress_count"] - entry["reviewed_no_progress"] >= entry["contract"]["budget"]["max_no_progress"]
            if spent or stalled:
                review = value.get("reassessment", {})
                _text(review.get("reason"), "reassessment.reason")
                _text(review.get("strategy_change"), "reassessment.strategy_change")
                extension = review.get("additional_attempts", 0)
                _require(type(extension) is int and extension >= 0 and (not spent or extension > 0), "A spent budget needs a positive additional_attempts allowance")
                entry["attempt_limit"] += extension
                entry["reviewed_no_progress"] = entry["no_progress_count"]
        for resolution in value.get("resolutions", []):
            cid = resolution.get("claim_id")
            _require(cid in entry["contract"]["claim_ids"], "Resolution claim is outside task scope")
            _text(resolution.get("reason"), "resolution.reason")
            correction = _selected_evidence(root, entry, resolution.get("evidence_indices"), cid)
            challenges = state["claims"][cid]["challenges"]
            match = [item for item in challenges if item["id"] == resolution.get("challenge_id") and not item["resolved"]]
            _require(len(match) == 1, "Resolution must identify one unresolved challenge")
            _require(match[0]["task_id"] != task_id or match[0]["attempt"] < len(entry["attempts"]), "A challenge needs corrective evidence returned after its originating attempt; the same result cannot clear its own blocker")
            origin = {(item["path"], item["revision"]) for item in match[0].get("origin_evidence", [])}
            _require(any((item["path"], item["revision"]) not in origin for item in correction), "Resolution must cite a new artifact or revision, not recycle the challenged evidence")
            match[0]["resolved"] = True
            match[0]["resolution"] = {"task_id": task_id, "attempt": len(entry["attempts"]), "reason": resolution["reason"], "evidence_indices": resolution["evidence_indices"]}
        for promotion in value.get("promotions", []):
            cid, level = promotion.get("claim_id"), promotion.get("level")
            _require(cid in entry["contract"]["claim_ids"] and level in LEVELS, "Promotion claim/level is outside task scope or invalid")
            _require(action in {"accept", "narrow"}, "Promotion needs accepted or narrowed requester disposition")
            _text(promotion.get("reason"), "promotion.reason")
            claim = state["claims"][cid]
            _require(all(_fresh(root, locator) for locator in entry["contract"]["inputs"]), "Task inputs changed or disappeared; refresh the contract and rerun before promotion")
            _require(not _dependency_issues(root, state, entry["contract"], cid), "; ".join(_dependency_issues(root, state, entry["contract"], cid)))
            _require(not any(not item["resolved"] for item in claim["challenges"]), f"Claim {cid} has unresolved blockers/counterevidence; no promotion")
            selected = _selected_evidence(root, entry, promotion.get("evidence_indices"), cid, level)
            claim["support"][level] = [{**item, "task_id": task_id, "attempt": len(entry["attempts"]), "reason": promotion["reason"]} for item in selected]
            claim["status"] = "supported"
        for update in value.get("claim_updates", []):
            cid = update.get("claim_id")
            _require(cid in entry["contract"]["claim_ids"] and update.get("status") in {"narrowed", "parked", "invalidated"}, "claim_updates may retire/limit only claims in this task scope")
            _text(update.get("reason"), "claim_update.reason")
            state["claims"][cid]["status"] = update["status"]
            state["claims"][cid]["limitations"].append(update["reason"])
            _propagate_invalidations(state, {cid}, f"Coordinator {update['status']} claim {cid}: {update['reason']}")
        entry["decisions"].append({**value, "attempt": len(entry["attempts"]), "time": _now()})
        entry["status"] = ACTIONS[action]
        _commit(directory, state, "decide", {"task_id": task_id, "attempt": len(entry["attempts"]), "action": action, "reason": value["reason"]})
        return entry


def context(project: str | Path, task_id: str | None = None) -> dict:
    """Compact recovery/delegation context; deliberately omits full event history."""
    root, _, state = _read(project)
    result = {"schema_version": 1, "revision": state["revision"], "project": state["project"], "research": state["research"], "rules": ["Return evidence and changed understanding, not a self-issued claim PASS.", "Keep blockers scoped to affected claims; report negative results normally.", "At the return limit, hand off limitations and a next discriminating question.", "Only coordinator imports results/decisions into shared state."]}
    if task_id:
        entry = state["tasks"].get(task_id)
        _require(entry is not None, "Unknown task id")
        value = copy.deepcopy(entry["contract"])
        for locator in value["inputs"]:
            locator["fresh"] = _fresh(root, locator)
        result.update({"task": value, "status": entry["status"], "next_attempt": len(entry["attempts"]) + 1, "attempt_limit": entry["attempt_limit"], "no_progress_count": entry["no_progress_count"], "claims": {cid: state["claims"][cid] for cid in value["claim_ids"]}, "latest_result": entry["attempts"][-1] if entry["attempts"] else None, "latest_decision": entry["decisions"][-1] if entry["decisions"] else None})
    else:
        result.update({"claims": state["claims"], "tasks": {tid: {"role": item["contract"]["role"], "question": item["contract"]["question"], "status": item["status"], "attempts": len(item["attempts"])} for tid, item in state["tasks"].items()}})
    return result


def audit(project: str | Path) -> dict:
    """Report actual handoff/evidence risks, without manufacturing a scientific PASS."""
    root, directory = _paths(project)
    with _locked(directory):
        _, _, state = _read(project)
        risks = []
        def add(code: str, message: str, blocking: bool = True, **scope):
            risks.append({"code": code, "message": message, "blocking": blocking, **scope})
        entries = _events(directory)
        if [item["seq"] for item in entries] != list(range(1, state["revision"] + 1)):
            add("journal_gap", "State and journal sequence differ")
        for tid, entry in state["tasks"].items():
            supports_current_claim = any(claim["status"] == "supported" and any(item.get("task_id") == tid for items in claim["support"].values() for item in items) for claim in state["claims"].values())
            live = entry["status"] not in CLOSED or supports_current_claim
            if entry["status"] == "awaiting_decision":
                add("unclosed_handoff", "Result awaits requester disposition", task_id=tid)
            for locator in entry["contract"]["inputs"]:
                if not _fresh(root, locator):
                    add("stale_input", f"Input is missing or changed: {locator['path']}", blocking=live, task_id=tid)
            for result in entry["attempts"]:
                for item in result["evidence"]:
                    if not _fresh(root, item):
                        is_support = any(claim["status"] == "supported" and any(ref["path"] == item["path"] and ref["revision"] == item["revision"] for refs in claim["support"].values() for ref in refs) for cid, claim in state["claims"].items() if cid in item["claim_ids"])
                        add("stale_evidence", f"Evidence is missing or changed: {item['path']}", blocking=entry["status"] not in CLOSED or is_support, task_id=tid, attempt=result["attempt"], claim_ids=item["claim_ids"])
            dependency_issues = _dependency_issues(root, state, entry["contract"])
            if dependency_issues:
                add("invalid_dependency", "; ".join(dependency_issues), blocking=live, task_id=tid)
            if entry["status"] == "active" and len(entry["attempts"]) >= entry["attempt_limit"]:
                add("budget_exhausted", "Task is active beyond its approved attempt budget", task_id=tid)
        for cid, claim in state["claims"].items():
            unresolved = [item for item in claim["challenges"] if not item["resolved"]]
            if unresolved:
                add("unresolved_challenge", "Claim has unresolved blocker or counterevidence", blocking=claim["status"] in {"hypothesis", "supported"}, claim_ids=[cid], challenge_ids=[item["id"] for item in unresolved])
            if claim["status"] == "supported":
                valid = bool(claim["support"]) and all(level in LEVELS and _claim_current(root, state, cid, level) for level in claim["support"])
                if not valid:
                    add("unsupported_claim", "Supported claim lacks current matching evidence or has unresolved challenge", claim_ids=[cid])
        return {"schema_version": 1, "revision": state["revision"], "protocol_ok": not any(item["blocking"] for item in risks), "scientific_validity": "not_judged", "risks": risks}
