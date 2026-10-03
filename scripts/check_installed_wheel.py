"""Run the built distribution outside the checkout, including bundled skills."""
from __future__ import annotations

import os
from pathlib import Path
import subprocess
import sys
import tempfile


def main():
    root = Path(__file__).resolve().parents[1]
    directory = Path(sys.argv[1]).resolve() if len(sys.argv) > 1 else root / "dist"
    wheels = list(directory.glob("research_assistant_maf-*.whl"))
    if len(wheels) != 1:
        raise RuntimeError("Use a directory containing exactly one built project wheel")
    with tempfile.TemporaryDirectory(prefix="research-assistant-wheel-") as temporary:
        workspace = Path(temporary)
        target = workspace / "installed"
        subprocess.run([sys.executable, "-m", "pip", "install", "--no-deps", "--target", str(target), str(wheels[0])], check=True)
        environment = {**os.environ, "PYTHONPATH": str(target)}
        code = (
            "from pathlib import Path; import research_assistant.engine as e; "
            "import research_assistant.guidance as g; import re; "
            "from research_assistant.cli import main; "
            "assert Path(e.__file__).is_relative_to(Path.cwd()/'installed'); "
            "assert '# Simulation Evidence' in e.role_text('simulation'); "
            "assert '# Research Coordinator' in e.role_text('coordinator'); "
            "assert (Path(e.__file__).parent/'resources/skills/research-coordinator/references/execution.md').is_file(); "
            "scope={'mode':'audit','sections':['full_manuscript']}; "
            "text=e.role_text('writer',scope); "
            "assert '# Introduction' in text and '# Writing Review' in text; "
            "assert '# Scientific objects and sentence continuity' in text; "
            "assert '# Chapter responsibilities and evidence-dependent writing' in text; "
            "assert '# Active evidence supplementation and return' in text; "
            "assert 'Selected criteria: continuity, title, abstract, introduction, methods, results-discussion-conclusions.' in text; "
            "intro=e.role_text('writer',{'mode':'revise','sections':['introduction']}); "
            "excerpt=intro.split('Selected criteria: continuity, introduction.',1)[1].split('Assigned writing method source:',1)[0]; "
            "assert '<a id=\"continuity\"></a>' in excerpt and '<a id=\"introduction\"></a>' in excerpt; "
            "assert '<a id=\"methods\"></a>' not in excerpt and '<a id=\"abstract\"></a>' not in excerpt; "
            "assert '# Active evidence supplementation and return' in e.role_text('writer'); "
            "assert '# Scientific Writing Core' not in e.role_text('literature'); "
            "root=g.resource_root(); "
            "paths=[root/'skills'/s/'SKILL.md' for s in g.selected_skills('writer',scope)]; "
            "assert all((p.parent/link.split('#')[0]).is_file() for p in paths for link in re.findall(r'\\]\\(([^)]+)\\)',p.read_text(encoding='utf-8'))); "
            "assert all((root/'skills/scientific-writing/references'/name).is_file() for name in ['institution-guidance.md','source-ledger.md','object-and-continuity.md','chapter-contracts.md','cohesion-source-ledger.md','section-specific-guidance.md']); "
            "raise SystemExit(main(['demo',str(Path.cwd()/'demo')]))"
        )
        subprocess.run([sys.executable, "-c", code], cwd=workspace, env=environment, check=True)


if __name__ == "__main__":
    main()
