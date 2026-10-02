"""Save the actual final JSON from a located completed/interrupted SDK thread.

Extraction does not accept its science or replay work. The coordinator still
checks original artifacts and uses explicit CLI reconciliation.
"""
import argparse
import asyncio
import json
from pathlib import Path
from openai_codex import AsyncCodex, AsyncThread


async def execute(args):
    async with AsyncCodex() as client:
        response = await AsyncThread(client, args.thread_id).read(include_turns=True)
        for turn in reversed(response.thread.turns):
            for item in reversed(turn.items):
                item = getattr(item, 'root', item)
                phase = getattr(item, 'phase', None)
                phase = getattr(phase, 'value', phase)
                if getattr(item, 'type', None) == 'agentMessage' and phase == 'final_answer':
                    value = json.loads(item.text)
                    args.output.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
                    print(json.dumps({'actual_response_file': str(args.output), 'evidence': value.get('evidence'), 'status': str(turn.status)}, ensure_ascii=True))
                    return
        raise ValueError('No final structured response found; inspect without synthesizing one')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('thread_id')
    parser.add_argument('output', type=Path)
    asyncio.run(execute(parser.parse_args()))
