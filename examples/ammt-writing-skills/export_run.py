"""Publish actual authored candidates and compact, truthful execution scope.

Run after coordinator inspection. No source PDFs, publisher extracts, frozen
raw inputs or complete prompt traces are copied. ResearchFlow receives the
same execution summary so requester evaluation can close the handoff.
"""
import argparse
import json
from pathlib import Path
import shutil
from research_assistant import state


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('--paper', type=Path, required=True)
    args = parser.parse_args()
    project = args.project.resolve()
    output = Path(__file__).resolve().parent
    ledger = json.loads((project / '.research-assistant/execution.json').read_text(encoding='utf-8'))
    scientific = json.loads((project / '.research-assistant/research-state.json').read_text(encoding='utf-8'))
    calls = []
    for key, call in ledger['calls'].items():
        request = call['request']
        packet = json.loads(request['prompt'])
        calls.append({'request_id': key, 'role': request['role'], 'status': call['status'],
                      'thread_id': call.get('thread_id'), 'progress': call.get('progress', []),
                      'response': call.get('response'),
                      'writing': packet.get('writing', packet.get('task', {}).get('writing'))})
    attempts = scientific['tasks']['R4_FRONTMATTER']['attempts']
    if not attempts:
        raise ValueError('No actual registered writing return to export')
    latest = len(attempts)
    for source, target in [('outputs/frontmatter.tex', f'outputs/attempt-{latest}-frontmatter.tex')]:
        if (project / source).is_file():
            (output / target).parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(project / source, output / target)
    for path in (project / 'reviews/R4_FRONTMATTER').glob('attempt-*.json'):
        shutil.copy2(path, output / 'outputs' / (path.stem + '-review.json'))
    summary = {
        'date': '2026-10-02', 'status': ledger['status'], 'cycles': ledger['cycles'],
        'calls': calls, 'registered_writer_attempts': latest,
        'writer_task_status': scientific['tasks']['R4_FRONTMATTER']['status'],
        'protocol_audit': state.audit(project),
        'interventions': [
            'Initial writer used former fixed timer: 358.7s and 300s turns interrupted; explicit same-thread continuations produced files and a 35.9s structured return.',
            'Initial reviewer also interrupted by former timer. Coordinator inspected original thread, asked why return was pending, received ready-to-report diagnostic, then requested a real review preserving context.',
            'Recovery reviewer read another actual reader evaluation; its initial evidence-first assessment and later exposure are disclosed in its returned limitations.',
            'Structured original returns reconciled explicitly; resumed native graph uses new progress checkpoints and latest section guides.',
            'Attempt-2 writer completed and replied to a real non-cancelling checkpoint. Its return was rejected for an appended line locator in evidence.path; report-only correction retained line 250 in summary and the exact declared source file. Original rejected return is preserved separately; no scientific work was replayed.'
        ],
        'evaluation_scope': 'Same-case editorial application with closely related guide examples; initial candidate partly autonomous. No unseen transfer, randomized comparison, measured efficiency gain, human peer review or independent thermal validation.',
        'canonical_manuscript': 'ResearchFlow paper/ammt-study/manuscript.tex, separately integrated and independently reviewed; the forward candidate does not silently replace it.',
        'private_materials': 'Original publisher PDFs, full page extracts, local field arrays and frozen manuscript inputs remain outside this public export.',
    }
    encoded = json.dumps(summary, ensure_ascii=False, indent=2) + '\n'
    (output / 'execution-summary.json').write_text(encoded, encoding='utf-8')
    destination = args.paper.resolve() / 'revision-r4/forward-use/execution-summary.json'
    destination.write_text(encoded, encoding='utf-8')
    print(json.dumps({'status': summary['status'], 'attempts': latest, 'calls': len(calls), 'summary': str(output / 'execution-summary.json')}, ensure_ascii=True))


if __name__ == '__main__':
    main()
