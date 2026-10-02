"""Explicit same-worker finalization after inspecting an interrupted turn.

Not an automatic retry: the caller must inspect the recorded thread/artifacts
first, then explicitly supply --confirmed-interrupted. Preserve previous reads
and output contract; write the real returned JSON for CLI reconciliation.
"""
from pathlib import Path
import argparse
import asyncio
import json
from openai_codex import AsyncCodex
from research_assistant.engine import validate
from research_assistant.providers import CodexProvider, _strict_output_schema


async def execute(args):
    project = args.project.resolve()
    ledger = json.loads((project / '.research-assistant/execution.json').read_text(encoding='utf-8'))
    call = ledger['calls'][args.request_id]
    if call['status'] not in {'failed', 'interrupted'} or not call.get('thread_id'):
        raise ValueError('Only a located failed/interrupted call with a known thread can be finalized')
    if not args.confirmed_interrupted:
        raise ValueError('Inspect thread completion/artifacts first, then explicitly confirm the interrupted status')
    client = AsyncCodex()
    turn = None
    provider = CodexProvider(timeout_seconds=args.timeout)
    provider.thread_ids[args.request_id] = call['thread_id']
    try:
        thread = await client.thread_resume(call['thread_id'])
        # Investigate the delayed return before prescribing finalization. This
        # status question resumes the located interrupted context; it is not a
        # new assignment or evidence that elapsed time demonstrated a loop.
        diagnostic_turn = await thread.turn(
            'Coordinator recovery inquiry: why did the prior turn not return? '
            'State your current activity, actual candidate, remaining question '
            'and value of continuation. Slow reasoning is grounds to continue; '
            'repeated polish should return the current best candidate. '
            'Answer briefly from existing context without private reasoning.',
        )
        diagnostic = await provider.wait_for_turn(diagnostic_turn, args.request_id + ':recovery-status')
        print(json.dumps({'recovery_status': diagnostic.final_response}, ensure_ascii=True), flush=True)
        message = (
            'The coordinator inspected your interrupted turn: the original-source checks were substantive, '
            'but neither contracted output file exists. Continue from the material already read. '
            'Complete outputs/frontmatter.tex and outputs/editorial-note.md now, using the existing source/evidence scope. '
            'The contracted title/abstract/Introduction candidate is the next useful contribution. '
            'Reserve additional reading for a consequential unresolved assertion, otherwise keep a source-supported '
            'statement or record a bounded source question in the note. Do not restart the investigation, change '
            'scientific quantities, launch another agent, or edit shared state. After actual files exist, '
            'return the original RESULT schema with attempt 1. The coordinator will read the files and reconcile '
            'the interrupted request explicitly; this finalization does not certify the text.')
        if args.report_only:
            if not all((project / p).is_file() for p in ['outputs/frontmatter.tex', 'outputs/editorial-note.md']):
                raise ValueError('Report-only finalization requires the actual existing outputs')
            message = ('The coordinator inspected the second interrupted turn and the actual two files '
                       'you wrote: outputs/frontmatter.tex and outputs/editorial-note.md. Both artifacts exist. '
                       'Your writing assignment has produced the candidate and note; now return only the '
                       'original RESULT JSON for attempt 1 with those actual evidence paths, level observation, '
                       'kind observation, claim_ids empty. Describe editorial contribution and remaining limits. '
                       'Do not use tools, reread sources, modify files, polish prose or perform more research. '
                       'changed_understanding is false for editorial-only work. This is a report finalization '
                       'of actual artifacts, not scientific acceptance. The independent reader review will follow.')
        turn = await thread.turn(
            message,
            output_schema=_strict_output_schema(call['request']['output_schema']),
        )
        result = await provider.wait_for_turn(turn, args.request_id)
        response = json.loads(result.final_response)
        validate(response, call['request']['output_schema'])
        args.response.parent.mkdir(parents=True, exist_ok=True)
        args.response.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'finalized_thread': call['thread_id'], 'request_id': args.request_id,
                          'actual_response': str(args.response.resolve()), 'status': str(result.status)}))
    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--project', required=True, type=Path)
    parser.add_argument('--request-id', required=True)
    parser.add_argument('--response', required=True, type=Path)
    parser.add_argument('--confirmed-interrupted', action='store_true')
    parser.add_argument('--report-only', action='store_true', help='Finalize JSON only after inspecting existing outputs')
    parser.add_argument('--timeout', type=int, default=300, help='Non-cancelling progress checkpoint interval')
    args = parser.parse_args()
    asyncio.run(execute(args))


if __name__ == '__main__':
    main()
