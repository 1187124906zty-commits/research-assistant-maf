"""Small usable entry point for the independent MAF research assistant."""
from __future__ import annotations

import argparse
import asyncio
import json
from pathlib import Path
import sys

from . import state


def print_json(value, *, stream=None):
    stream = stream or sys.stdout
    rendered = json.dumps(value, ensure_ascii=False, indent=2)
    try:
        rendered.encode(getattr(stream, "encoding", None) or "utf-8")
    except UnicodeEncodeError:
        # A Windows legacy code page must not turn a completed run into a
        # reported failure merely because a scientific symbol is unencodable.
        rendered = json.dumps(value, ensure_ascii=True, indent=2)
    print(rendered, file=stream)


def main(argv=None):
    parser = argparse.ArgumentParser(prog="research-assistant")
    sub = parser.add_subparsers(dest="command", required=True)
    run = sub.add_parser("run", help="Start or continue a bounded MAF research session")
    run.add_argument("project", type=Path)
    run.add_argument("--brief", required=True)
    run.add_argument("--max-cycles", type=int, default=4)
    run.add_argument("--parallel", type=int, default=2)
    run.add_argument("--provider", choices=["codex"], default="codex")
    run.add_argument("--codex-bin")
    run.add_argument("--timeout", type=float, default=600)
    resume = sub.add_parser("resume", help="Reconcile current state; do not replay unknown calls")
    resume.add_argument("project", type=Path)
    resume.add_argument("--codex-bin")
    resume.add_argument("--timeout", type=float, default=600)
    resume.add_argument("--additional-cycles", type=int, default=0,
                        help="Explicitly reopen a budget/needs-input return after its prerequisites are handled")
    for name in ("demo", "status"):
        sub.add_parser(name).add_argument("project", type=Path)
    reconcile = sub.add_parser("reconcile", help="Bind an inspected result to an uncertain role call")
    reconcile.add_argument("project", type=Path)
    reconcile.add_argument("request_id")
    reconcile.add_argument("response", type=Path)
    reconcile.add_argument("--reason", required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "status":
            data = state._load(args.project / ".research-assistant/execution.json")
            output = {"status": data["status"], "message": data["message"], "cycles": data["cycles"],
                      "deliverables": data["deliverables"], "checkpoint": data["checkpoint"],
                      "calls": {key: {"status": value["status"], "thread_id": value.get("thread_id")}
                                for key, value in data["calls"].items()}, "audit": state.audit(args.project)}
        elif args.command == "reconcile":
            from .engine import ExecutionError, bind_response, execution_lock
            directory = args.project.resolve() / ".research-assistant"
            with execution_lock(directory):
                ledger = state._load(directory / "execution.json")
                call = ledger["calls"][args.request_id]
                if call["status"] == "completed":
                    raise ExecutionError("Completed calls cannot be replaced")
                response = state._load(args.response)
                artifacts = bind_response(args.project.resolve(), call["request"], response)
                call.update(status="completed", response=response, artifacts=artifacts, reconciliation_reason=args.reason)
                state._atomic(directory / "execution.json", ledger)
                output = {"request_id": args.request_id, "status": "reconciled", "reason": args.reason}
        else:
            from .engine import run_project
            if args.command == "demo":
                from .demo import DemoProvider
                provider = DemoProvider()
                output = asyncio.run(run_project(args.project, provider,
                    brief="Demonstrate bounded parallel work, negative evidence and scoped writing", max_cycles=4, parallel=2))
            else:
                from .providers import CodexProvider
                provider = CodexProvider(args.codex_bin, args.timeout)
                if args.command == "resume":
                    saved = state._load(args.project / ".research-assistant/execution.json")
                    output = asyncio.run(run_project(args.project, provider, resume=True,
                        max_cycles=saved["max_cycles"], parallel=saved["parallel"], additional_cycles=args.additional_cycles))
                else:
                    output = asyncio.run(run_project(args.project, provider, brief=args.brief,
                        max_cycles=args.max_cycles, parallel=args.parallel))
            output = {key: output[key] for key in ("status", "message", "cycles", "deliverables", "checkpoint")}
        print_json(output)
        return 0 if output.get("status") in {"complete", "reconciled"} else 2
    except Exception as exc:
        print_json({"error": str(exc)}, stream=sys.stderr)
        return 1
