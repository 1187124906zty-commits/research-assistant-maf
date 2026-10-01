"""Repeat the bounded manuscript-input workflow with real configured Codex calls."""
from pathlib import Path
import argparse
import asyncio
import json
import shutil
from research_assistant import state
from research_assistant.engine import run_project
from research_assistant.providers import CodexProvider

async def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--project',type=Path,required=True)
    args=parser.parse_args()
    root=args.project.resolve()
    inputs=Path(__file__).resolve().parent/'inputs'
    brief=('Prepare only two bounded English manuscript inputs from the frozen evidence: outputs/mechanism-analysis.md and outputs/results-discussion.md. '
           'Original numerical case was performed with SimAgent. No PDE runs, browsing, source edits or invented citations. '
           'Run separate review and requester disposition, repair consequential local defects within the two-attempt budget, '
           'and complete after both inputs are delivered. Actual full-article assembly is separate. '
           'No claim IDs or physical-validation promotion. Use actual declared file paths in evidence.path, with line/JSON pointers in summary. '
           'You are not alone: write only the assigned paths and never revert others edits.')
    if (root/'.research-assistant').exists():
        raise SystemExit('Use a fresh project for this example; use the CLI resume/reconcile commands for an existing session.')
    (root/'inputs').mkdir(parents=True,exist_ok=True)
    for name in ('evidence-dossier.md','verified-data.json'):
        shutil.copy2(inputs/name,root/'inputs'/name)
    state.initialize(root,brief)
    for tid,role,path,question in (
        ('AMMT_MECHANISM','mechanism','outputs/mechanism-analysis.md','Interpret the fixed-B factorial, rear boundaries and surviving explanations without real melt-flow causal attribution.'),
        ('AMMT_WRITING','writer','outputs/results-discussion.md','Draft 1200-1800 words of Results/Discussion with scoped geometry, B/C speed, passage time and property-continuation responses.')):
        state.task(root,{'id':tid,'role':role,'question':question,'purpose':'Provide an evidence-bound manuscript input',
            'claim_ids':[],'inputs':[{'path':'inputs/evidence-dossier.md'},{'path':'inputs/verified-data.json'}],
            'outputs':[path],'writes':[path], 'acceptance':['Located values, exact data roles, actual output file, honest missing evidence'],
            'budget':{'max_attempts':2,'max_no_progress':2},'depends_on':[]})
    result=await run_project(root,CodexProvider(timeout_seconds=900),brief=brief,max_cycles=3,parallel=2)
    print(json.dumps({k:result[k] for k in ('status','message','cycles','deliverables')},ensure_ascii=True,indent=2))

if __name__=='__main__':asyncio.run(main())
