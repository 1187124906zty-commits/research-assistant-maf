"""One explicit Codex schema smoke; no manuscript work or scientific claims."""
import asyncio
import json
from pathlib import Path
import tempfile

from research_assistant import schemas
from research_assistant.demo import DemoProvider
from research_assistant.engine import validate
from research_assistant.providers import CodexProvider


async def main():
    contract = DemoProvider.contract("writing-schema-probe", "writer", [], "manuscript/probe.md")
    contract["writing"] = {"mode": "revise", "sections": ["introduction"]}
    with tempfile.TemporaryDirectory(prefix="writing-schema-probe-") as directory:
        provider = CodexProvider(timeout_seconds=120)
        response = await provider.ask({"role": "coordinator",
            "instructions": "This is a schema compatibility check. Do not use tools, read project files, create a manuscript or execute the supplied contract. Return the requested JSON object exactly.",
            "prompt": "Return this object, including its explicit optional writing selection:\n" + json.dumps(contract),
            "cwd": str(Path(directory).resolve()), "output_schema": schemas.CONTRACT,
            "request_id": "optional-writing-schema-smoke"})
        validate(response, schemas.CONTRACT)
        if response != contract:
            raise RuntimeError("Schema smoke returned a changed contract")
        print(json.dumps({"optional_writing_schema": "accepted", "thread_id": provider.last_thread_id,
                          "scientific_or_writing_quality": "not_assessed"}))


if __name__ == "__main__":
    asyncio.run(main())
