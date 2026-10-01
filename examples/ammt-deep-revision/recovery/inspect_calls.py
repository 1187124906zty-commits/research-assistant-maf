"""Read-only native Codex call diagnosis, no turns or credential dumps."""
import asyncio
import json
from pathlib import Path

from openai_codex import AsyncCodex, AsyncThread
from research_assistant.engine import validate


ROOT = Path(__file__).resolve().parents[3]
WORKSPACE = ROOT / "local-runs/ammt-deep-revision/drafts"
OWNED = Path(__file__).resolve().parent


def public_path(value):
    """Keep project-relative provenance, redact external machine locators."""
    path = Path(value)
    if not path.is_absolute():
        path = WORKSPACE / path
    try:
        return path.resolve().relative_to(WORKSPACE.resolve()).as_posix()
    except ValueError:
        return "<external-input>"


async def main():
    ledger = json.loads((WORKSPACE / ".research-assistant/execution.json").read_text(encoding="utf-8"))
    results = {"model_turns_started": 0, "workspace": "local-runs/ammt-deep-revision/drafts", "ledger_status": ledger["status"], "calls": {}}
    async with AsyncCodex() as client:
        for key, call in ledger["calls"].items():
            if not key.startswith("worker:") or not call.get("thread_id"):
                continue
            response = await AsyncThread(client, call["thread_id"]).read(include_turns=True)
            thread = response.thread
            current_status = getattr(thread, "status", None)
            current_status = getattr(current_status, "root", current_status)
            diagnosis = {
                "ledger_status": call["status"],
                "thread_status": getattr(current_status, "type", None),
                "turn_statuses": [], "structured_response_recovered": False,
            }
            for turn in thread.turns:
                status = getattr(turn.status, "value", turn.status)
                diagnosis["turn_statuses"].append({"status": status, "item_count": len(turn.items)})
            for turn in reversed(thread.turns):
                candidates = []
                for item in reversed(turn.items):
                    entry = getattr(item, "root", item)
                    if getattr(entry, "type", None) != "agentMessage":
                        continue
                    phase = getattr(getattr(entry, "phase", None), "value", getattr(entry, "phase", None))
                    if phase == "final_answer":
                        candidates.insert(0, entry.text)
                    elif phase is None:
                        candidates.append(entry.text)
                for text in candidates:
                    try:
                        parsed = json.loads(text)
                        validate(parsed, call["request"]["output_schema"])
                    except Exception:
                        continue
                    name = key.split(":")[1].lower() + "-recovered.json"
                    (OWNED / name).write_text(text, encoding="utf-8")
                    diagnosis.update(structured_response_recovered=True, local_response_filename=name,
                                     response_turn_status=getattr(turn.status, "value", turn.status),
                                     evidence_paths=[public_path(item["path"]) for item in parsed["evidence"]])
                    break
                if diagnosis["structured_response_recovered"]:
                    break
            results["calls"][key] = diagnosis
    (OWNED / "call-diagnosis.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(results, ensure_ascii=True, indent=2))


asyncio.run(main())
