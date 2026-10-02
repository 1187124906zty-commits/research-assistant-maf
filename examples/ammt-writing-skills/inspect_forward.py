"""Read only compact turn status and latest activity of the saved native calls."""
import argparse
import asyncio
import json
from pathlib import Path
from openai_codex import AsyncCodex, AsyncThread


async def inspect(project):
    ledger=json.loads((project/'.research-assistant/execution.json').read_text(encoding='utf-8'))
    async with AsyncCodex() as client:
        for key, call in ledger['calls'].items():
            if not call.get('thread_id'):
                continue
            response=await AsyncThread(client,call['thread_id']).read(include_turns=True)
            turns=[]
            for turn in response.thread.turns:
                recent=[]
                for item in turn.items[-5:]:
                    entry=getattr(item,'root',item)
                    recent.append({'type':getattr(entry,'type',None),
                                   'message':getattr(entry,'text','')[:600],
                                   'command':getattr(entry,'command','')[:180]})
                turns.append({'status':str(turn.status),'items':len(turn.items),'recent':recent})
            print(json.dumps({'request':key,'status':call['status'],'turns':turns},ensure_ascii=True))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('project',type=Path)
    asyncio.run(inspect(parser.parse_args().project.resolve()))
