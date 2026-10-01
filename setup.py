"""Ship this project's role/skill sources as resources, without global installs."""
from pathlib import Path
import shutil

from setuptools import setup
from setuptools.command.build_py import build_py


class BuildWithResources(build_py):
    def run(self):
        super().run()
        destination = Path(self.build_lib) / "research_assistant" / "resources"
        for source in ("roles", "skills"):
            shutil.copytree(Path(__file__).parent / source, destination / source, dirs_exist_ok=True)


setup(cmdclass={"build_py": BuildWithResources})
