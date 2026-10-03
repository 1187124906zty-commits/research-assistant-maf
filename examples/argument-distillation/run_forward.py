"""New bounded AMMT forward revision using the real MAF graph and Codex.

No solver calls, canonical manuscript edits, or desired replacement supplied.
The default source is the sibling case; use --paper for another retained copy.
--prepare-only writes a reviewable manifest and does not invoke a model.
"""
import argparse
import asyncio
import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]


def prepare(paper: Path, workspace: Path, timeout: int, extra_inputs: list[Path]) -> Path:
    bindings = [
        (paper / "manuscript.tex", "inputs/manuscript.tex"),
        (paper / "evidence/verified-data.json", "inputs/verified-data.json"),
        (paper / "evidence/evidence-dossier.md", "inputs/evidence-dossier.md"),
    ]
    bindings.extend((path, f"inputs/source-{i}-{path.name}") for i, path in enumerate(extra_inputs))
    for source, _ in bindings:
        if not source.is_file():
            raise ValueError(f"Missing retained input: {source}")
    if workspace.exists():
        raise ValueError("Use a new workspace; inspect any unknown original call before resuming")
    manifest = {
        "brief": "Revise the retained AMMT Methods and Results/Discussion as an evidence-bound argument for neighboring-field readers. Read the assigned writing guidance, actual manuscript and retained evidence. Complete a bounded prose revision and located reasoning note; do not execute simulations, invent evidence, broaden the study or edit the canonical manuscript. An editorial acceptance never establishes new physical validation. Stop after the contracted candidate, independent reviewer and requester disposition.",
        "inputs": [{"source": str(source.resolve()), "path": target} for source, target in bindings],
        "timeout_seconds": timeout, "max_cycles": 3, "parallel": 1,
        "tasks": [{
            "id": "DISTILLATION_AMMT", "role": "writer",
            "question": "How can the retained Methods and Results/Discussion explain the comparison and answer without repeated reporting shells or lost scientific conditions?",
            "purpose": "Forward-use evaluation on actual retained research; preserve quantitative disagreements and data roles while improving paragraph logic and precision.",
            "writing": {"mode": "revise", "sections": ["methods_results", "discussion_conclusions"]},
            "outputs": ["outputs/methods-results-discussion.tex", "outputs/revision-note.md"],
            "writes": ["outputs/"],
            "acceptance": [
                "Return complete assigned Methods and Results/Discussion sections, keeping existing citation keys valid. Reader can reconstruct why the design and each principal comparison answer the question.",
                "Preserve actual calibration/condition-comparison roles, observable definitions, numerical adequacy scope, property-continuation assumptions and contrary findings; interpret conflicting source statements through original records rather than copying conclusions.",
                "Provide a located before/after note for at least three substantive paragraph repairs, stating reader decision, proposition/support, retained conditions and compression consequence. No acceptance by keyword, word count, or presence of connectors.",
                "No new solver runs, unobserved mechanism, blind validation, universal accuracy claim, or unique inverse identification. Return unresolved source/evidence questions distinctly.",
            ],
            "budget": {"max_attempts": 2, "max_no_progress": 2},
        }],
    }
    workspace.parent.mkdir(parents=True, exist_ok=True)
    path = workspace.parent / f"{workspace.name}-manifest.json"
    with path.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
    return path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--paper", type=Path, default=ROOT.parent / "research-workflow/paper/ammt-study")
    parser.add_argument("--workspace", type=Path, required=True)
    parser.add_argument("--evidence", type=Path, action="append", default=[])
    parser.add_argument("--timeout", type=int, default=360)
    parser.add_argument("--prepare-only", action="store_true")
    args = parser.parse_args()
    workspace = args.workspace.resolve()
    manifest_path = prepare(args.paper.resolve(), workspace, args.timeout, args.evidence)
    if args.prepare_only:
        print(json.dumps({"manifest": str(manifest_path), "model_invoked": False}))
        return
    spec = importlib.util.spec_from_file_location("bounded_sections", ROOT / "examples/ammt-deep-revision/run_sections.py")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    asyncio.run(module.execute(manifest_path, workspace))


if __name__ == "__main__":
    main()
