"""Forward-use case on an unmodified earlier manuscript, using the real MAF graph.

Requires the sibling ResearchFlow case or --paper. Keeps inputs and model calls
in an explicit new workspace; never edits the canonical manuscript. The task
supplies evidence and the user problem, but no intended replacement prose.
"""
from pathlib import Path
import argparse
import asyncio
import importlib.util
import json


ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--paper', type=Path, default=ROOT.parent / 'research-workflow/paper/ammt-study')
    parser.add_argument('--workspace', required=True, type=Path)
    parser.add_argument('--timeout', type=int, default=360)
    args = parser.parse_args()
    paper = args.paper.resolve()
    workspace = args.workspace.resolve()
    # The frozen R3 input predates the new guides and R4 repair, preventing the
    # task from simply reusing the coordinator's intended candidate.
    inputs = [
        ('revision-r4/manuscript-input.tex', 'inputs/manuscript-r3.tex'),
        ('evidence/verified-data.json', 'inputs/verified-data.json'),
        ('revision-r3/citations/support-ledger.json', 'inputs/support-ledger.json'),
    ]
    manifest = {
        'brief': 'Perform one bounded title/abstract/introduction revision of the supplied AMMT research manuscript. Use assigned project writing guides and actual evidence. Make the central problem and research line understandable to neighboring-field readers; synthesize findings instead of an inventory of values, and relate existing research to the present study. Preserve calibration roles, measurement definitions, numerical/physical boundaries and negative findings. Produce the contracted candidate and a located editorial/evidence note. This is a forward-use evaluation of one writing assignment; conclude after reviewer and requester disposition when the contract is satisfied. Additional simulations, reference-count targets, journal submission and a full-paper autonomous pipeline are outside this assignment.',
        'inputs': [{'source': str(paper / source), 'path': target} for source, target in inputs],
        'timeout_seconds': args.timeout, 'max_cycles': 3, 'parallel': 1,
        'tasks': [{
            'id': 'R4_FRONTMATTER', 'role': 'writer',
            'question': 'How should the title, abstract and introduction present this existing study as a continuous evidence-supported argument?',
            'purpose': 'Evaluate actual use of the distributed writing methods on a previous manuscript, without providing the desired revised answer.',
            'writing': {'mode': 'revise', 'sections': ['title_abstract', 'introduction']},
            'outputs': ['outputs/frontmatter.tex', 'outputs/editorial-note.md'],
            'writes': ['outputs/'],
            'acceptance': ['Actual complete LaTeX title, abstract and Introduction candidate. Keep quantities/conditions accurate and existing keys valid where used; select source-supported information by section purpose rather than repeating every original value/key.',
                           'Located note separates editorial repairs, source uncertainty and evidence gaps; inspect originals/references where consequential.',
                           'No fabricated accuracy gains, latent measurements, held-out validation or causal mechanism.'],
            'budget': {'max_attempts': 2, 'max_no_progress': 2},
        }],
    }
    workspace.parent.mkdir(parents=True, exist_ok=True)
    manifest_path = workspace.parent / (workspace.name + '-manifest.json')
    if workspace.exists():
        raise SystemExit('Use a new workspace; inspect an interrupted run before an explicit new attempt.')
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    spec = importlib.util.spec_from_file_location('ammt_run_sections', ROOT / 'examples/ammt-deep-revision/run_sections.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    asyncio.run(module.execute(manifest_path, workspace))


if __name__ == '__main__':
    main()
