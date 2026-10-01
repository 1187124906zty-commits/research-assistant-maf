"""Run bounded, versioned manuscript contracts on the real MAF graph.

The coordinator prepares the manifest after reading and accepting upstream
research. This script freezes those actual files; it does not invent a gap,
select a journal, rerun a PDE, or certify the final paper.
"""
from pathlib import Path
import argparse
import asyncio
import json
import shutil

from research_assistant import state
from research_assistant.engine import run_project
from research_assistant.providers import CodexProvider


async def execute(manifest_path: Path, workspace: Path):
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    workspace.mkdir(parents=True, exist_ok=True)
    if (workspace / ".research-assistant/research-state.json").exists():
        raise SystemExit("Workspace already has a run. Inspect its ledger before resuming; do not overwrite accepted inputs.")
    frozen = []
    for item in manifest["inputs"]:
        source = Path(item["source"]).resolve()
        target = (workspace / item["path"]).resolve()
        if not source.is_file() or not target.is_relative_to(workspace):
            raise ValueError(f"Invalid input binding: {item['path']}")
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, target)
        frozen.append({"path": item["path"]})
    brief = manifest["brief"]
    state.initialize(workspace, brief)
    for contract in manifest["tasks"]:
        contract = {**contract, "inputs": frozen, "claim_ids": [], "depends_on": []}
        state.task(workspace, contract)
    provider = CodexProvider(timeout_seconds=manifest.get("timeout_seconds", 1500))
    result = await run_project(
        workspace, provider, brief=brief,
        max_cycles=manifest.get("max_cycles", 3),
        parallel=manifest.get("parallel", 2),
    )
    execution = json.loads((workspace / ".research-assistant/execution.json").read_text(encoding="utf-8"))
    summary = {
        "status": result["status"], "message": result["message"],
        "cycles": result["cycles"], "deliverables": result["deliverables"],
        "model_calls": len(execution["calls"]),
        "roles": [call["request"]["role"] for call in execution["calls"].values()],
        "call_statuses": {key: call["status"] for key, call in execution["calls"].items()},
        "protocol_audit": state.audit(workspace),
        "scope": "Manuscript assistance; root must read actual candidates and integrate/review the whole paper. No physical-evidence promotion.",
    }
    (workspace / "run-summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=True, indent=2))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True, type=Path)
    parser.add_argument("--workspace", required=True, type=Path)
    args = parser.parse_args()
    asyncio.run(execute(args.manifest.resolve(), args.workspace.resolve()))


if __name__ == "__main__":
    main()
