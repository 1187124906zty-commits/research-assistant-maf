"""Diagnose a previously interrupted review before a deliberate continuation.

This preserves the saved thread and records actual responses. It never applies
an elapsed-time cancellation to an active turn; explicit caller cancellation is
still respected. Inspection and reconciliation remain coordinator decisions.
"""
import argparse
import asyncio
import json
from pathlib import Path

from openai_codex import AsyncCodex
from research_assistant.engine import validate
from research_assistant.providers import _strict_output_schema


PROGRESS = {
    'type': 'object', 'additionalProperties': False,
    'properties': {
        'activity': {'type': 'string', 'enum': ['reasoning', 'evidence_check', 'repeated_revision', 'ready', 'blocked', 'unknown']},
        'reason_no_return': {'type': 'string'},
        'candidate_or_findings': {'type': 'string'},
        'remaining_question': {'type': 'string'},
        'next_step_value': {'type': 'string'},
    },
    'required': ['activity', 'reason_no_return', 'candidate_or_findings', 'remaining_question', 'next_step_value'],
}


async def execute(args):
    project = args.project.resolve()
    ledger = json.loads((project / '.research-assistant/execution.json').read_text(encoding='utf-8'))
    call = ledger['calls'][args.request_id]
    if call['status'] not in {'failed', 'interrupted'} or not call.get('thread_id'):
        raise ValueError('Requires a located failed/interrupted call after actual status inspection')
    args.response.parent.mkdir(parents=True, exist_ok=True)
    async with AsyncCodex() as client:
        thread = await client.thread_resume(call['thread_id'])
        question = (
            'Coordinator progress inquiry: your previous turn was interrupted by the former fixed timer. '
            'Elapsed time is not a reason to judge your work unsuccessful. Before deciding on continuation, '
            'please explain briefly why no structured return was produced. Are you still thinking through '
            'an unresolved review question, checking consequential evidence, repeatedly revising an existing '
            'candidate, ready to report, or blocked? State the concrete findings already available, the '
            'remaining question and what further work could change. Report concise task status, not private '
            'reasoning. Answer from your existing context; no new source search or manuscript edits are '
            'needed for this progress inquiry. The coordinator will use your answer to select the next step.')
        diagnostic_path = args.response.with_name(args.response.stem + '-diagnostic.json')
        if args.use_saved_diagnostic:
            saved = json.loads(diagnostic_path.read_text(encoding='utf-8'))
            if saved['thread_id'] != call['thread_id']:
                raise ValueError('Diagnostic does not belong to the saved review thread')
            diagnostic = saved['progress']
            validate(diagnostic, PROGRESS)
        else:
            turn = await thread.turn(question, output_schema=PROGRESS)
            result = await turn.run()
            diagnostic = json.loads(result.final_response)
            validate(diagnostic, PROGRESS)
            diagnostic_path.write_text(json.dumps({'thread_id': call['thread_id'], 'progress': diagnostic}, indent=2) + '\n', encoding='utf-8')
            print(json.dumps({'progress_inquiry': diagnostic}, ensure_ascii=True), flush=True)
        if args.diagnose_only:
            return
        # A human/coordinator invokes this second step deliberately after seeing
        # the diagnostic. Do not classify scientific sufficiency by a timer.
        if not args.continue_review:
            return
        message = (
            'The coordinator received your progress response. Complete the bounded review of the actual '
            'frontmatter candidate and return the original REVIEW schema. Use the source/evidence checks '
            'already made. If a consequential unresolved assertion remains, check that specific assertion; '
            'otherwise deliver the best current findings for the writer and coordinator. Identify located '
            'reader problems and minimal fixes, distinguishing editorial defects from scientific blockers. '
            'Do not repeatedly polish the review or certify an unrendered candidate PDF. Do not edit the '
            'canonical manuscript or shared state. The next writer revision will use these findings, '
            'so this handoff need not resolve optional wording preferences itself.')
        if args.other_review:
            message += (
                ' A separate reader evaluation is available at ' + str(args.other_review.resolve()) +
                '. Read its located abstract-selection and Introduction-objective findings and assess '
                'them against the actual candidate. The writer was asked for a synthesized argument, '
                'so evaluate collective reader burden as well as individual numerical correctness. '
                'Use your own judgment and disclose this additional reviewer exposure; do not simply '
                'adopt its recommendations or treat reader defects as scientific counterevidence.')
        turn = await thread.turn(message, output_schema=_strict_output_schema(call['request']['output_schema']))
        result = await turn.run()
        response = json.loads(result.final_response)
        validate(response, call['request']['output_schema'])
        args.response.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'response': str(args.response.resolve()), 'status': str(result.status)}), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', type=Path, required=True)
    parser.add_argument('--request-id', required=True)
    parser.add_argument('--response', type=Path, required=True)
    parser.add_argument('--diagnose-only', action='store_true')
    parser.add_argument('--continue-review', action='store_true')
    parser.add_argument('--use-saved-diagnostic', action='store_true')
    parser.add_argument('--other-review', type=Path)
    asyncio.run(execute(parser.parse_args()))
