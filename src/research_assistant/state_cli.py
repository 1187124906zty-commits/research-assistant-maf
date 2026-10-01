"""Small JSON-first command interface; see docs/API.md for exact contracts."""

import argparse
import json
import sys
from pathlib import Path

from . import state as runtime


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(prog="researchflow", description="Evidence-bound research memory and task handoffs (no LLM calls)")
    parser.add_argument("--actor", help="Coordinator protocol identity; not OS authentication")
    sub = parser.add_subparsers(dest="command", required=True)
    init = sub.add_parser("init", help="Initialize persistent research memory")
    init.add_argument("project")
    init.add_argument("--question", required=True)
    init.add_argument("--config", type=Path)
    init.add_argument("--coordinator", default="coordinator")
    for name in ("plan", "task"):
        command = sub.add_parser(name)
        command.add_argument("project")
        command.add_argument("json_file", type=Path)
    for name in ("record", "decide"):
        command = sub.add_parser(name)
        command.add_argument("project")
        command.add_argument("task_id")
        command.add_argument("json_file", type=Path)
    ctx = sub.add_parser("context")
    ctx.add_argument("project")
    ctx.add_argument("--task")
    snap = sub.add_parser("snapshot", help="Generate file revision locators")
    snap.add_argument("project")
    snap.add_argument("paths", nargs="+")
    check = sub.add_parser("audit")
    check.add_argument("project")
    args = parser.parse_args(argv)
    try:
        payload = runtime._load(args.json_file) if hasattr(args, "json_file") else None
        if args.command == "init":
            result = runtime.initialize(args.project, args.question, runtime._load(args.config) if args.config else None, args.coordinator)
        elif args.command in ("plan", "task"):
            result = getattr(runtime, args.command)(args.project, payload, args.actor)
        elif args.command in ("record", "decide"):
            result = getattr(runtime, args.command)(args.project, args.task_id, payload, args.actor)
        elif args.command == "context":
            result = runtime.context(args.project, args.task)
        elif args.command == "snapshot":
            result = runtime.snapshot(args.project, args.paths)
        else:
            result = runtime.audit(args.project)
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 2 if args.command == "audit" and not result["protocol_ok"] else 0
    except (runtime.GovernanceError, TypeError, KeyError, AttributeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
