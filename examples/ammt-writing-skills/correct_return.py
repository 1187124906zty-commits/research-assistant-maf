"""Request a report-only correction after inspecting a real rejected return.

No scientific task is replayed. The original response remains preserved;
corrected JSON must still pass the original schema and artifact bindings.
"""
import argparse
import asyncio
import json
from pathlib import Path
from openai_codex import AsyncCodex
from research_assistant.engine import validate, bind_response
from research_assistant.providers import CodexProvider, _strict_output_schema


async def execute(args):
    project = args.project.resolve()
    ledger = json.loads((project / '.research-assistant/execution.json').read_text(encoding='utf-8'))
    call = ledger['calls'][args.request_id]
    if call['status'] != 'failed' or not call.get('thread_id'):
        raise ValueError('Requires a known failed return after actual thread/artifact inspection')
    original = json.loads(args.original.read_text(encoding='utf-8'))
    validate(original, call['request']['output_schema'])
    provider = CodexProvider(timeout_seconds=120)
    provider.thread_ids[args.request_id] = call['thread_id']
    async with AsyncCodex() as client:
        thread = await client.thread_resume(call['thread_id'])
        turn = await thread.turn(
            'Your actual attempt-2 files and structured final were inspected. The scientific writing task '
            'has returned. One report field was rejected: evidence.path "inputs/manuscript-r3.tex:250" '
            'is not the declared file path. The contract requires evidence.path to be an actual file, '
            'and line locators to appear in its summary. Return the same RESULT JSON for attempt 2, '
            'using evidence.path "inputs/manuscript-r3.tex" and retaining line 250 and the same '
            'counterevidence in its summary. Preserve all other evidence meanings and limitations. '
            'This is a report-format correction only. Do not use tools, edit the candidate, reread sources, '
            'run a solver, change evidence levels or claim new understanding. No scientific retry is '
            'authorized by this report correction. The coordinator will explicitly reconcile the actual '
            'corrected return and continue the already pending reviewer handoff.',
            output_schema=_strict_output_schema(call['request']['output_schema']))
        result = await provider.wait_for_turn(turn, args.request_id)
        response = json.loads(result.final_response)
        validate(response, call['request']['output_schema'])
        bind_response(project, call['request'], response)
        args.output.write_text(json.dumps(response, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        print(json.dumps({'corrected_actual_return': str(args.output), 'status': str(result.status)}, ensure_ascii=True))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project', type=Path)
    parser.add_argument('request_id')
    parser.add_argument('original', type=Path)
    parser.add_argument('output', type=Path)
    asyncio.run(execute(parser.parse_args()))
