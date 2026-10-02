"""Actual MAF fork/join workflow around an authoritative scientific state.

The provider runs bounded roles. Program checks enforce recorded contracts, not
scientific truth or operating-system isolation. Unknown calls are not replayed.
"""
from __future__ import annotations

import asyncio
import copy
from contextlib import contextmanager
import inspect
import json
import os
from pathlib import Path
from typing import Any

from agent_framework import Executor, FileCheckpointStorage, WorkflowBuilder, WorkflowContext, handler

from . import schemas, state, guidance


class ExecutionError(RuntimeError):
    pass


def validate(value: Any, schema: dict, location: str = "response") -> None:
    """Validate the deliberately small JSON-schema subset used in this project."""
    if "anyOf" in schema:
        for variant in schema["anyOf"]:
            try:
                validate(value, variant, location)
                return
            except ExecutionError:
                pass
        raise ExecutionError(f"{location}: does not match permitted variants")
    types = schema.get("type", [])
    types = [types] if isinstance(types, str) else types
    allowed = {"object": isinstance(value, dict), "array": isinstance(value, list),
               "string": isinstance(value, str), "boolean": type(value) is bool,
               "integer": type(value) is int, "null": value is None}
    if types and not any(allowed.get(kind, False) for kind in types):
        raise ExecutionError(f"{location}: expected {types}")
    if "enum" in schema and value not in schema["enum"]:
        raise ExecutionError(f"{location}: invalid enum value")
    if isinstance(value, dict):
        properties = schema.get("properties", {})
        if set(schema.get("required", [])) - value.keys():
            raise ExecutionError(f"{location}: missing required fields")
        if schema.get("additionalProperties") is False and set(value) - properties.keys():
            raise ExecutionError(f"{location}: unexpected fields")
        for key, item in value.items():
            if key in properties:
                validate(item, properties[key], f"{location}.{key}")
    if isinstance(value, list):
        for index, item in enumerate(value):
            validate(item, schema.get("items", {}), f"{location}[{index}]")


@contextmanager
def execution_lock(directory: Path):
    """One runner at a time; scientific state has its own transaction lock."""
    stream = (directory / "execution.lock").open("a+b")
    if stream.tell() == 0:
        stream.write(b"0")
        stream.flush()
    stream.seek(0)
    locked = False
    try:
        if os.name == "nt":
            import msvcrt
            msvcrt.locking(stream.fileno(), msvcrt.LK_NBLCK, 1)
        else:
            import fcntl
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        locked = True
        yield
    except OSError as exc:
        raise ExecutionError("Another runner is using this project, or execution lock failed") from exc
    finally:
        if locked:
            stream.seek(0)
            if os.name == "nt":
                import msvcrt
                msvcrt.locking(stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(stream.fileno(), fcntl.LOCK_UN)
        stream.close()


def role_text(role: str, writing: dict | None = None) -> str:
    try:
        return guidance.load_role(role, writing)
    except ValueError as exc:
        raise ExecutionError(str(exc)) from exc


def packet_writing(packet: dict) -> dict | None:
    """Scope is explicit metadata; no keyword guessing or manuscript inspection."""
    if "writing" in packet:
        return packet["writing"]
    if isinstance(packet.get("task"), dict):
        return packet["task"].get("writing")
    if isinstance(packet.get("handoff"), dict):
        return packet_writing(packet["handoff"])
    return None


@contextmanager
def progress_journal(session):
    """Persist public checkpoint events while keeping caller decision callbacks.

    One runner owns this provider during a project run. Parallel role events
    bind to their request IDs; progress does not mutate scientific evidence.
    """
    provider = session.provider
    if not hasattr(provider, "progress_callback"):
        yield
        return
    original = provider.progress_callback

    async def record(event):
        key = event["request_id"]
        if key in session.data["calls"]:
            call = session.data["calls"][key]
            call.setdefault("progress", []).append(copy.deepcopy(event))
            call["thread_id"] = event.get("thread_id")
            session.save()
        if original is not None:
            result = original(copy.deepcopy(event))
            return await result if inspect.isawaitable(result) else result
        return None

    provider.progress_callback = record
    try:
        yield
    finally:
        provider.progress_callback = original


class Session:
    def __init__(self, project, provider, *, brief: str | None = None,
                 max_cycles: int = 4, parallel: int = 2, max_context_chars: int = 60000):
        self.root = Path(project).resolve()
        self.directory = self.root / ".research-assistant"
        self.provider = provider
        if type(max_cycles) is not int or max_cycles < 1 or type(parallel) is not int or not 1 <= parallel <= 4:
            raise ExecutionError("max_cycles must be positive; parallel must be between 1 and 4")
        self.path = self.directory / "execution.json"
        if not (self.directory / "research-state.json").is_file():
            if not brief or not brief.strip():
                raise ExecutionError("A new project requires a research brief")
            state.initialize(self.root, brief)
        if self.path.is_file():
            self.data = state._load(self.path)
            if brief is not None and brief != self.data["brief"]:
                raise ExecutionError("Resume keeps the original brief; update scientific state explicitly")
            if parallel != self.data["parallel"]:
                raise ExecutionError("Resume must use the saved parallel setting")
        else:
            self.data = {"schema_version": 1, "brief": brief or state.context(self.root)["project"]["question"],
                         "parallel": parallel, "max_cycles": max_cycles, "cycles": 0,
                         "status": "ready", "calls": {}, "batch": [], "checkpoint": None,
                         "events": [], "deliverables": [], "message": ""}
        self.max_context_chars = max_context_chars

    def save(self):
        state._atomic(self.path, self.data)

    def event(self, kind: str, **fields):
        self.data["events"].append({"kind": kind, **fields})
        self.save()

    def request(self, role: str, packet: dict, schema: dict, request_id: str) -> dict:
        prompt = json.dumps(packet, ensure_ascii=False, indent=2)
        if len(prompt) > self.max_context_chars:
            raise ExecutionError("Context exceeds the configured bound; narrow the packet without dropping evidence")
        writing = packet_writing(packet)
        instructions = role_text(role, writing)
        if role == "reviewer" and packet.get("writing_review") is True and writing is None:
            instructions += guidance.skill_text("scientific-writing")
            instructions += guidance.skill_text("paper-writing-review")
        return {"role": role, "instructions": instructions +
                "\nUse only the assigned writes. Never edit .research-assistant shared state. "
                "Read consequential original inputs; return one JSON object matching the supplied schema. "
                "Evidence.path must name the exact actual file path; put page, line and JSON-pointer locators in its summary, not appended to the filename. "
                "Keep facts, assumptions and scientific support separate.",
                "prompt": prompt, "cwd": str(self.root), "output_schema": schema, "request_id": request_id}

    async def ask(self, role: str, packet: dict, schema: dict, key: str) -> dict:
        calls = self.data["calls"]
        request = self.request(role, packet, schema, key)
        if key in calls:
            call = calls[key]
            if call["status"] == "completed":
                # Project transaction numbers can change as an independent sibling
                # returns. All substantive packet fields must still match.
                def binding(item):
                    body = json.loads(item["prompt"])
                    body.pop("revision", None)
                    # Saved calls retain the instructions actually used. New skill
                    # versions apply to new calls, not to replayed cached responses.
                    return {key: value for key, value in {**item, "prompt": body}.items()
                            if key not in {"instructions", "output_schema"}}
                if binding(call["request"]) != binding(request):
                    raise ExecutionError(f"Call {key} context changed; its cached response is not current")
                for artifact in call.get("artifacts", []):
                    if not state._fresh(self.root, artifact):
                        raise ExecutionError(f"Call {key} artifact changed after its response; inspect before importing")
                validate(call["response"], schema)
                return copy.deepcopy(call["response"])
            raise ExecutionError(f"Call {key} has unknown/failed completion; inspect its thread/artifacts before an explicit new attempt")
        calls[key] = {"status": "started", "request": request}
        self.save()
        try:
            response = await self.provider.ask(request)
            validate(response, schema)
            artifacts = bind_response(self.root, request, response)
        except BaseException as exc:
            calls[key]["error_type"] = type(exc).__name__
            calls[key]["status"] = "interrupted" if isinstance(exc, (asyncio.CancelledError, KeyboardInterrupt)) else "failed"
            calls[key]["thread_id"] = getattr(self.provider, "thread_ids", {}).get(key)
            calls[key]["progress"] = copy.deepcopy(getattr(self.provider, "progress_records", {}).get(key, calls[key].get("progress", [])))
            self.save()
            raise
        calls[key].update(status="completed", response=response, artifacts=artifacts,
                          thread_id=getattr(self.provider, "thread_ids", {}).get(key))
        calls[key]["progress"] = copy.deepcopy(getattr(self.provider, "progress_records", {}).get(key, calls[key].get("progress", [])))
        self.save()
        self.event("role_completed", role=role, request_id=key)
        return response

    def worker_context(self, tid: str) -> dict:
        packet = state.context(self.root, tid)
        contract = packet["task"]
        if not all(item["fresh"] for item in contract["inputs"]):
            raise ExecutionError(f"Task {tid} has changed inputs; do not run its old contract")
        _, _, current = state._read(self.root)
        issues = state._dependency_issues(self.root, current, contract)
        if issues:
            raise ExecutionError("; ".join(issues))
        if packet["next_attempt"] > packet["attempt_limit"]:
            raise ExecutionError(f"Task {tid} exhausted its attempt budget")
        packet["brief"] = self.data["brief"]
        packet["instruction"] = "Answer the bounded task, create its output artifacts, report contribution and cost; return at its budget."
        feedback = self.review_feedback(tid)
        if feedback is not None:
            packet["review_feedback"] = feedback
            packet["instruction"] += " Inspect located reviewer findings and return specific repairs or evidence-based disagreements within this task's scope."
        return packet

    def review_feedback(self, tid: str) -> dict | None:
        """Located, version-checked feedback for continued or newly routed work."""
        current = state._read(self.root)[2]
        entry = current["tasks"][tid]
        if not entry["attempts"]:
            return None
        rid = f"review-{tid}-{len(entry['attempts'])}"
        review_entry = current["tasks"].get(rid)
        if not review_entry or not review_entry["attempts"]:
            return None
        artifact = review_entry["attempts"][-1]["evidence"][0]
        if not state._fresh(self.root, artifact):
            raise ExecutionError(f"Task {tid} reviewer feedback changed; inspect before reuse")
        return {"path": artifact["path"], "revision": artifact["revision"],
                "report": state._load(self.root / artifact["path"])}

    async def review(self, tid: str) -> dict:
        packet = state.context(self.root, tid)
        report = packet["latest_result"]
        attempt = len(state._read(self.root)[2]["tasks"][tid]["attempts"])
        rid = f"review-{tid}-{attempt}"
        review_path = self.root / "reviews" / tid / f"attempt-{attempt}.json"
        current = state._read(self.root)[2]
        if rid not in current["tasks"]:
            state.task(self.root, {"id": rid, "role": "reviewer", "question": packet["task"]["question"],
                "purpose": "Independently check this return against original evidence before requester disposition",
                "claim_ids": packet["task"]["claim_ids"],
                "inputs": [{"path": item["path"], "revision": item["revision"]} for item in report["evidence"]],
                "outputs": [str(review_path.relative_to(self.root))],
                "acceptance": ["Located findings, affected claims and feasible corrections; optional polish separated"],
                "budget": {"max_attempts": 1, "max_no_progress": 1}})
        if state.context(self.root, rid)["status"] == "active":
            review_packet = {"question": packet["task"]["question"], "purpose": packet["task"]["purpose"],
                             "acceptance": packet["task"]["acceptance"], "claims": packet["claims"],
                             "original_inputs": packet["task"]["inputs"],
                             "evidence": report["evidence"], "outputs": packet["task"]["outputs"],
                             "write_path": str(review_path.relative_to(self.root)),
                             "instruction": "Read the actual evidence. Producer interpretation is withheld from this first-pass review. Findings name exact affected claims; disclose unavailable evidence."}
            if packet["task"].get("writing") is not None:
                review_packet["writing"] = {**packet["task"]["writing"], "mode": "audit"}
            elif packet["task"]["role"] == "writer":
                # Legacy writer tasks get compact common review guidance without
                # selecting every section of an unspecified manuscript.
                review_packet["instruction"] += " Audit reader logic, evidence scope and located source support."
                review_packet["writing_review"] = True
            review = await self.ask("reviewer", review_packet, schemas.REVIEW, f"review:{tid}:{attempt}")
            review_path.parent.mkdir(parents=True, exist_ok=True)
            state._atomic(review_path, review)
            cids = set(packet["task"]["claim_ids"])
            blockers = []
            for finding in review["findings"]:
                if not set(finding["claim_ids"]) <= cids:
                    raise ExecutionError("Review finding names a claim outside its task")
                if finding["blocking"] and finding["claim_ids"]:
                    blockers.append({"claim_ids": finding["claim_ids"], "reason": finding["reason"], "kind": "review"})
            state.record(self.root, rid, {"attempt": 1, "changed_understanding": bool(review["findings"]),
                "reason": review["summary"], "evidence": [{"path": str(review_path.relative_to(self.root)),
                    "level": "observation", "kind": "observation", "claim_ids": list(cids), "summary": "Independent review report; not supporting physical evidence"}], "blockers": blockers})
        if state.context(self.root, rid)["status"] == "awaiting_decision":
            state.decide(self.root, rid, {"action": "accept", "reason": "Review findings received and preserved for requester disposition"})
        return state._load(review_path)

    async def dispose(self, tid: str):
        packet = state.context(self.root, tid)
        if packet["status"] != "awaiting_decision":
            return
        review = await self.review(tid)
        packet = state.context(self.root, tid)
        attempt = len(state._read(self.root)[2]["tasks"][tid]["attempts"])
        disposition_packet = {"brief": self.data["brief"], "handoff": packet,
            "independent_review": review,
            "instruction": "Interpret contribution to the whole project. Accepting delivery is separate from promotion. Respond to blocking findings; preserve negative evidence. Continuing needs a new discriminating purpose when budget/stall limits are reached."}
        decision = await self.ask("coordinator", disposition_packet, schemas.DECISION, f"decide:{tid}:{attempt}")
        for correction in range(2):
            try:
                # Manuscripts without claim IDs still need blocking defects addressed.
                if any(f["blocking"] and not f["claim_ids"] for f in review["findings"]) and decision["action"] == "accept":
                    raise ExecutionError("Blocking unscoped review finding requires a correction or documented reframe/park")
                applicable = {key: value for key, value in decision.items()
                              if key != "reassessment" or value is not None}
                state.decide(self.root, tid, applicable)
                break
            except (state.GovernanceError, ExecutionError) as exc:
                if correction:
                    raise
                # A known invalid decision has no committed science effects. Send
                # one exact guard finding back; never replay an uncertain call.
                self.event("disposition_rejected", task_id=tid, reason=str(exc))
                decision = await self.ask("coordinator", {**disposition_packet,
                    "rejected_decision": decision, "guard_feedback": str(exc),
                    "correction_instruction": "Return one corrected disposition, using existing evidence only. Promotion indices must each name kind=support at the exact requested level and claim. Source observations can inform your interpretation but are not supporting promotion indices. No new files, experiments, or relaxed evidence rules. If evidence is inadequate, accept delivery without promotion, narrow, reframe or park with reasons."},
                    schemas.DECISION, f"decide:{tid}:{attempt}:correction:1")
        self.event("requester_disposition", task_id=tid, action=decision["action"], reason=decision["reason"])


class Coordinator(Executor):
    def __init__(self, session: Session, workers: list[str]):
        super().__init__(id="coordinator")
        self.session, self.workers = session, workers

    @handler
    async def coordinate(self, message: dict, ctx: WorkflowContext[dict, dict]):
        session = self.session
        current = state._read(session.root)[2]
        # Resume scientific dispositions from fresh state, independently of an old checkpoint.
        for tid, entry in list(current["tasks"].items()):
            if entry["status"] == "awaiting_decision" and entry["contract"]["role"] != "reviewer":
                await session.dispose(tid)
        if session.data["batch"]:
            previous = state._read(session.root)[2]
            if all(previous["tasks"][tid]["status"] != "awaiting_decision" and
                   len(previous["tasks"][tid]["attempts"]) >= session.data.get("batch_attempts", {}).get(tid, 1)
                   for tid in session.data["batch"]):
                session.data["cycles"] += 1
                session.data["batch"] = []
                session.save()
        if session.data["cycles"] >= session.data["max_cycles"]:
            session.data.update(status="budget_reached", message="Bounded session returned for reassessment; this is not scientific acceptance")
            session.save()
            await ctx.yield_output(session.data)
            return
        current = state._read(session.root)[2]
        active = [tid for tid, entry in current["tasks"].items()
                  if entry["status"] == "active" and entry["contract"]["role"] != "reviewer"]
        if not active:
            # Compact synthesis and summaries; originals remain available through locators.
            packet = state.context(session.root)
            packet["brief"] = session.data["brief"]
            packet["remaining_cycles"] = session.data["max_cycles"] - session.data["cycles"]
            packet["max_ready_tasks"] = len(self.workers)
            packet["returns"] = [{"task_id": tid, "contribution": entry["attempts"][-1].get("contribution"),
                                   "decision": entry["decisions"][-1] if entry["decisions"] else None,
                                   "review_feedback": session.review_feedback(tid)}
                                  for tid, entry in current["tasks"].items()
                                  if entry["attempts"] and entry["contract"]["role"] != "reviewer"]
            packet["instruction"] = "Choose the next informative action. Delegate only ready tasks, up to max_ready_tasks. Add new claim IDs only; preserve facts/uncertainties. Work can be literature, simulation, mechanism or writer. For manuscript work, set optional task.writing with mode draft/revise/audit and explicit sections title_abstract/introduction/methods_results/discussion_conclusions/full_manuscript. Treat reviewer feedback as bounded new repair tasks with source locators, rather than replaying saved calls; choose literature for source support, mechanism for explanatory scope, writer for repairs and reviewer for recheck. Complete only with actual requested deliverables; otherwise return needs_input with the specific missing prerequisite."
            proposal = await session.ask("coordinator", packet, schemas.PLAN,
                                         f"plan:{current['revision']}:{session.data['cycles']}:{session.data.get('generation', 0)}")
            if proposal["action"] != "work":
                if proposal["tasks"]:
                    raise ExecutionError("A terminal proposal cannot also dispatch tasks")
                if proposal["action"] == "complete":
                    if not proposal["deliverables"]:
                        raise ExecutionError("Completion requires actual deliverable paths")
                    for name in proposal["deliverables"]:
                        path = (session.root / name).resolve()
                        if not path.is_relative_to(session.root) or not path.is_file():
                            raise ExecutionError("Completion deliverables must be files inside this project")
                    if not state.audit(session.root)["protocol_ok"]:
                        raise ExecutionError("Unresolved protocol risks prevent final delivery")
                session.data.update(status=proposal["action"], message=proposal["reason"], deliverables=proposal["deliverables"])
                session.save()
                await ctx.yield_output(session.data)
                return
            if not 1 <= len(proposal["tasks"]) <= len(self.workers):
                raise ExecutionError("Proposal must contain a bounded nonempty ready batch")
            for contract in proposal["tasks"]:
                # Null is a model output variant, not a scientific level declaration.
                for dependency in contract["depends_on"]:
                    if dependency["required_level"] is None:
                        dependency.pop("required_level")
            state.dispatch_batch(session.root, proposal["plan"], proposal["tasks"])
            active = [contract["id"] for contract in proposal["tasks"]]
        selected = active[:len(self.workers)]
        batch_id = f"batch-{session.data['cycles']}"
        session.data["batch"] = selected
        session.data["batch_attempts"] = {tid: state.context(session.root, tid)["next_attempt"] for tid in selected}
        session.data["status"] = "running"
        session.data["message"] = ""
        session.save()
        for worker, tid in zip(self.workers, selected):
            session.worker_context(tid)  # Preflight all registered inputs/budgets before dispatch.
            await ctx.send_message({"task_id": tid, "batch_id": batch_id, "batch_size": len(selected)}, target_id=worker)
        session.event("batch_dispatched", tasks=selected, batch_id=batch_id)


class Worker(Executor):
    def __init__(self, session: Session, number: int):
        super().__init__(id=f"worker-{number}")
        self.session = session

    @handler
    async def run_task(self, message: dict, ctx: WorkflowContext[dict]):
        session, tid = self.session, message["task_id"]
        packet = session.worker_context(tid)
        role = packet["task"]["role"]
        report = await session.ask(role, packet, schemas.RESULT, f"worker:{tid}:{packet['next_attempt']}")
        if report["attempt"] != packet["next_attempt"]:
            raise ExecutionError("Worker returned the wrong attempt")
        await ctx.send_message({**message, "report": report}, target_id="collector")


class Collector(Executor):
    def __init__(self, session: Session):
        super().__init__(id="collector")
        self.session = session
        self.batches: dict[str, dict] = {}

    @handler
    async def collect(self, message: dict, ctx: WorkflowContext[dict]):
        batch = self.batches.setdefault(message["batch_id"], {})
        batch[message["task_id"]] = message["report"]
        if len(batch) < message["batch_size"]:
            return
        for tid, report in batch.items():
            status = state.context(self.session.root, tid)["status"]
            if status == "active":
                call = self.session.data["calls"][f"worker:{tid}:{report['attempt']}"]
                bindings = {item["path"]: item for item in call["artifacts"]}
                bound_report = copy.deepcopy(report)
                for item in bound_report["evidence"]:
                    binding = bindings[item["path"]]
                    if not state._fresh(self.session.root, binding):
                        raise ExecutionError("Worker artifact changed while awaiting batch collection")
                    item["revision"] = binding["revision"]
                state.record(self.session.root, tid, bound_report)
            elif status != "awaiting_decision":
                raise ExecutionError("Received a result for an already closed task")
        del self.batches[message["batch_id"]]
        await ctx.send_message({"phase": "returned"}, target_id="coordinator")

    async def on_checkpoint_save(self) -> dict[str, Any]:
        return {"batches": self.batches}

    async def on_checkpoint_restore(self, saved: dict[str, Any]) -> None:
        self.batches = saved.get("batches", {})


async def run_project(project, provider, *, brief=None, max_cycles=4, parallel=2,
                      resume=False, max_context_chars=60000, additional_cycles=0) -> dict:
    directory = Path(project).resolve() / ".research-assistant"
    directory.mkdir(parents=True, exist_ok=True)
    with execution_lock(directory):
        session = Session(project, provider, brief=brief, max_cycles=max_cycles,
                          parallel=parallel, max_context_chars=max_context_chars)
        if type(additional_cycles) is not int or additional_cycles < 0:
            raise ExecutionError("additional_cycles must be a nonnegative integer")
        if additional_cycles:
            if session.data["status"] not in {"budget_reached", "needs_input"}:
                raise ExecutionError("An extension is for a returned session, not a completed or uncertain call")
            session.data["max_cycles"] += additional_cycles
            session.data["status"] = "ready"
            session.data["generation"] = session.data.get("generation", 0) + 1
            session.event("explicit_extension", additional_cycles=additional_cycles)
        session.save()
        if session.data["status"] in {"complete", "needs_input", "budget_reached"}:
            return session.data
        workers = [Worker(session, number) for number in range(parallel)]
        coordinator = Coordinator(session, [worker.id for worker in workers])
        collector = Collector(session)
        storage = FileCheckpointStorage(session.directory / "checkpoints")
        builder = WorkflowBuilder(name="research-team", start_executor=coordinator,
                                  checkpoint_storage=storage, output_from=[coordinator],
                                  max_iterations=6 * session.data["max_cycles"] + 8)
        for worker in workers:
            builder.add_edge(coordinator, worker).add_edge(worker, collector)
        workflow = builder.add_edge(collector, coordinator).build()
        try:
            # Re-enter through the coordinator so changed scientific state is always read.
            # Native checkpoints are saved as execution diagnostics; the durable call
            # ledger and state reconcile effects instead of replaying stale graph messages.
            with progress_journal(session):
                async for event in workflow.run(message={"phase": "resume" if resume else "start"}, stream=True):
                    if event.type == "superstep_completed":
                        latest = await storage.get_latest(workflow_name=workflow.name)
                        if latest:
                            session.data["checkpoint"] = latest.checkpoint_id
                            session.save()
                    if event.type == "output":
                        break
            if session.data["status"] == "running":
                raise ExecutionError("Workflow stopped before a disposition or bounded return")
        except Exception as exc:
            session.data.update(status="attention", message=str(exc))
            session.save()
            raise
        return session.data


def bind_response(root: Path, request: dict, response: dict) -> list[dict]:
    """Shared validation for live returns and explicitly inspected reconciliation."""
    validate(response, request["output_schema"])
    artifacts = []
    if request["role"] in schemas.ROLES:
        packet = json.loads(request["prompt"])
        contract = packet["task"]
        if any(not state._fresh(root, item) for item in contract["inputs"]):
            raise ExecutionError("Worker return has a changed frozen input")
        writes = [(root / value).resolve() for value in contract["writes"]]
        inputs = {(root / item["path"]).resolve(): item for item in contract["inputs"]}
        for item in response["evidence"]:
            path = (root / item["path"]).resolve()
            if not set(item["claim_ids"]) <= set(contract["claim_ids"]):
                raise ExecutionError("Worker evidence names claims outside its contract")
            if path in inputs:
                # Sources are read-only provenance, including explicitly declared
                # external papers. Never bind a changed input to a new version.
                original = {"path": item["path"], "revision": inputs[path]["revision"]}
                if not state._fresh(root, original):
                    raise ExecutionError("Worker evidence cites a changed frozen input")
                artifacts.append(original)
            elif path.is_relative_to(root) and any(path == owner or path.is_relative_to(owner) for owner in writes):
                artifacts.extend(state.snapshot(root, [item["path"]]))
            else:
                raise ExecutionError("Worker evidence must be inside declared writes or cite a declared frozen input")
    return artifacts
