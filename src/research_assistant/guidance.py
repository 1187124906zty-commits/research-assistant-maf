"""Explicit, task-scoped role/skill loading from checkout or wheel resources."""
from __future__ import annotations

from pathlib import Path
from typing import Any


SECTIONS = {
    "title_abstract": "paper-title-abstract",
    "introduction": "paper-introduction",
    "methods_results": "paper-methods-results",
    "discussion_conclusions": "paper-discussion-conclusions",
}
MODES = {"draft", "revise", "audit"}


def resource_root() -> Path:
    packaged = Path(__file__).parent / "resources"
    if (packaged / "roles").is_dir() and (packaged / "skills").is_dir():
        return packaged
    source = Path(__file__).resolve().parents[2]
    if (source / "roles").is_dir() and (source / "skills").is_dir():
        return source
    raise ValueError("Missing bundled role/skill resources")


def writing_selection(value: Any) -> dict | None:
    """Optional task metadata, never guessed from words in the brief/question."""
    if value is None:
        return None
    if not isinstance(value, dict) or set(value) != {"mode", "sections"}:
        raise ValueError("writing needs exactly mode and sections")
    if not isinstance(value["mode"], str) or value["mode"] not in MODES:
        raise ValueError("writing.mode must be draft, revise or audit")
    sections = value["sections"]
    if not isinstance(sections, list) or not sections or any(
            not isinstance(section, str) or section not in {*SECTIONS, "full_manuscript"}
            for section in sections):
        raise ValueError("writing.sections needs explicit supported section names")
    if len(set(sections)) != len(sections):
        raise ValueError("writing.sections cannot contain duplicates")
    if "full_manuscript" in sections and len(sections) != 1:
        raise ValueError("full_manuscript already selects all sections")
    return {"mode": value["mode"], "sections": list(sections)}


def selected_skills(role: str, writing: dict | None = None) -> list[str]:
    selected = {"coordinator": ["research-coordinator"],
                "simulation": ["simulation-evidence"]}.get(role, []).copy()
    scope = writing_selection(writing)
    if role != "writer" and scope is None:
        return selected
    selected.append("scientific-writing")
    if role in {"writer", "coordinator"}:
        selected.append("scientific-editor")
    if role == "reviewer" or (scope and scope["mode"] == "audit"):
        selected.append("paper-writing-review")
    if scope:
        sections = list(SECTIONS) if scope["sections"] == ["full_manuscript"] else scope["sections"]
        selected.extend(SECTIONS[section] for section in sections)
    return list(dict.fromkeys(selected))


def skill_text(skill: str, root: Path | None = None) -> str:
    path = (root or resource_root()) / "skills" / skill / "SKILL.md"
    if not path.is_file():
        raise ValueError(f"Missing bundled skill {skill}")
    return (f"\nApplicable skill source: {path}. Resolve linked references relative to "
            f"{path.parent}; read originals and needed references, not every linked guide.\n"
            + path.read_text(encoding="utf-8"))


def selected_references(role: str, writing: dict | None = None) -> list[str]:
    """Deliver consequential short methods, rather than relying only on links."""
    scope = writing_selection(writing)
    if scope is None:
        return []
    names = ["object-and-continuity.md"]
    if role == "coordinator" or scope["sections"] == ["full_manuscript"]:
        names.append("chapter-contracts.md")
    return names


def reference_text(name: str, root: Path | None = None) -> str:
    path = (root or resource_root()) / "skills" / "scientific-writing" / "references" / name
    if not path.is_file():
        raise ValueError(f"Missing bundled writing reference {name}")
    return (f"\nAssigned writing method source: {path}. Resolve its links relative to "
            f"{path.parent}.\n" + path.read_text(encoding="utf-8"))


def load_role(role: str, writing: dict | None = None) -> str:
    if role not in {"coordinator", "literature", "simulation", "mechanism", "writer", "reviewer"}:
        raise ValueError(f"Unknown role {role}")
    root = resource_root()
    path = root / "roles" / f"{role}.md"
    if not path.is_file():
        raise ValueError(f"Missing role charter {role}")
    content = path.read_text(encoding="utf-8")
    for skill in selected_skills(role, writing):
        content += skill_text(skill, root)
    for name in selected_references(role, writing):
        content += reference_text(name, root)
    if writing is not None:
        scope = writing_selection(writing)
        content += f"\nAssigned writing mode: {scope['mode']}; sections: {', '.join(scope['sections'])}. "
        content += "Apply only these sections; do not invent missing results or expand the assignment.\n"
        if role == "literature":
            content += "For source synthesis and citation verification, read the scientific-writing reference source-use.md.\n"
    return content
