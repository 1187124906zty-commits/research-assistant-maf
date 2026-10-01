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
            "from research_assistant.cli import main; "
            "assert Path(e.__file__).is_relative_to(Path.cwd()/'installed'); "
            "assert '# Simulation Evidence' in e.role_text('simulation'); "
            "assert '# Research Coordinator' in e.role_text('coordinator'); "
            "assert (Path(e.__file__).parent/'resources/skills/research-coordinator/references/execution.md').is_file(); "
            "raise SystemExit(main(['demo',str(Path.cwd()/'demo')]))"
        )
        subprocess.run([sys.executable, "-c", code], cwd=workspace, env=environment, check=True)


if __name__ == "__main__":
    main()
