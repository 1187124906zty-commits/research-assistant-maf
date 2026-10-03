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
SECTION_ANCHORS = {
    "title_abstract": ("title", "abstract"),
    "introduction": ("introduction",),
    "methods_results": ("methods", "results-discussion-conclusions"),
    "discussion_conclusions": ("results-discussion-conclusions",),
}
SECTION_REFERENCE = "section-specific-guidance.md"
DISTILLATION_REFERENCE = "argument-distillation.md"
LIBRARY_REFERENCE = "library-use.md"
EXAMPLE_REFERENCE = "paragraph-examples.md"
SOURCE_EXAMPLE_REFERENCE = "source-backed-exemplars.md"
EXAMPLE_ANCHORS = {
    "title_abstract": ("abstract-example",),
    "introduction": ("introduction-example",),
    "methods_results": ("methods-example", "results-example"),
    "discussion_conclusions": ("results-example",),
}


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


def skill_text(skill: str, root: Path | None = None, *, compact_section: bool = False) -> str:
    """Read a standalone skill, or its named route to canonical section criteria.

    Default behavior remains full text for existing callers. Role loading uses
    compact section envelopes because its selected criteria already teach the
    chapter job; standalone section skills remain available for other hosts.
    """
    path = (root or resource_root()) / "skills" / skill / "SKILL.md"
    if not path.is_file():
        raise ValueError(f"Missing bundled skill {skill}")
    body = path.read_text(encoding="utf-8")
    if compact_section and skill in SECTIONS.values():
        heading = next(line for line in body.splitlines() if line.startswith("# "))
        body = (heading + "\n\nThis section skill is selected. Its compact, canonical "
                "reader criteria and connected examples are supplied below for the assigned "
                "scope. Read the standalone source only when additional detail is needed.\n")
    return (f"\nApplicable skill source: {path}. Resolve linked references relative to "
            f"{path.parent}; read originals and needed references, not every linked guide.\n"
            + body)


def selected_references(role: str, writing: dict | None = None) -> list[str]:
    """Deliver consequential short methods, rather than relying only on links."""
    scope = writing_selection(writing)
    if scope is None:
        return ["evidence-supplement.md"] if role == "writer" else []
    names = ["object-and-continuity.md", SECTION_REFERENCE, DISTILLATION_REFERENCE,
             LIBRARY_REFERENCE, EXAMPLE_REFERENCE]
    if source_example_reference_anchors(scope):
        names.append(SOURCE_EXAMPLE_REFERENCE)
    if role in {"writer", "coordinator", "reviewer"}:
        names.append("evidence-supplement.md")
    if role == "coordinator" or scope["sections"] == ["full_manuscript"]:
        names.append("chapter-contracts.md")
    return names


def distillation_reference_anchors(writing: dict) -> list[str]:
    """Route reader decisions, not the source library's hundreds of entries."""
    scope = writing_selection(writing)
    if scope is None:
        raise ValueError("Argument distillation needs an explicit writing selection")
    sections = list(SECTIONS) if scope["sections"] == ["full_manuscript"] else scope["sections"]
    anchors = ["reader-task", "language-and-trimming"]
    if "introduction" in sections:
        anchors.append("source-synthesis")
    if any(section in sections for section in
           ("title_abstract", "methods_results", "discussion_conclusions")):
        anchors.append("comparison-and-inference")
    if any(section in sections for section in ("methods_results", "discussion_conclusions")):
        anchors.append("evidence-medium")
    return anchors


def library_reference_anchors(writing: dict) -> list[str]:
    """Scope reader-position contracts without loading a phrase library."""
    scope = writing_selection(writing)
    if scope is None:
        raise ValueError("Library decisions need an explicit writing selection")
    sections = list(SECTIONS) if scope["sections"] == ["full_manuscript"] else scope["sections"]
    anchors = ["selection-contract"]
    if "title_abstract" in sections:
        anchors.append("abstract-opening")
    if "introduction" in sections:
        anchors.append("introduction-bridge")
    if any(section in sections for section in ("title_abstract", "introduction", "methods_results")):
        anchors.append("model-introduction")
    return anchors


def section_reference_anchors(writing: dict) -> list[str]:
    """Select only the criteria relevant to the explicit section assignment."""
    scope = writing_selection(writing)
    if scope is None:
        raise ValueError("Section criteria need an explicit writing selection")
    sections = list(SECTIONS) if scope["sections"] == ["full_manuscript"] else scope["sections"]
    anchors = ["continuity"]
    anchors.extend(anchor for section in sections for anchor in SECTION_ANCHORS[section])
    return list(dict.fromkeys(anchors))


def example_reference_anchors(writing: dict) -> list[str]:
    """Deliver connected illustrative prose for the explicit reading task.

    Examples teach information order; their invented scientific content is not
    evidence. Source-backed passages, when supplied, still require original
    context and provenance checks through the optional library route.
    """
    scope = writing_selection(writing)
    if scope is None:
        raise ValueError("Paragraph examples need an explicit writing selection")
    sections = list(SECTIONS) if scope["sections"] == ["full_manuscript"] else scope["sections"]
    return list(dict.fromkeys(anchor for section in sections for anchor in EXAMPLE_ANCHORS[section]))


def source_example_reference_anchors(writing: dict) -> list[str]:
    """One source-backed move per supported section; remaining cards are optional."""
    scope = writing_selection(writing)
    if scope is None:
        raise ValueError("Source examples need an explicit writing selection")
    sections = list(SECTIONS) if scope["sections"] == ["full_manuscript"] else scope["sections"]
    selected = {"introduction": "ctx-001", "methods_results": "ctx-003",
                "discussion_conclusions": "ctx-004"}
    return [selected[section] for section in sections if section in selected]


def reference_text(name: str, root: Path | None = None, *, anchors: list[str] | None = None) -> str:
    path = (root or resource_root()) / "skills" / "scientific-writing" / "references" / name
    if not path.is_file():
        raise ValueError(f"Missing bundled writing reference {name}")
    content = path.read_text(encoding="utf-8")
    if anchors is not None:
        # The maintained Markdown anchors are also the public links used by skills.
        # Keep provenance at the top; fail on a broken link instead of omitting it.
        first = content.find('<a id="')
        if first < 0 or not anchors:
            raise ValueError(f"Missing section anchors in bundled writing reference {name}")
        selected = [content[:first].rstrip()]
        for anchor in anchors:
            marker = f'<a id="{anchor}"></a>'
            start = content.find(marker)
            if start < 0 or content.find(marker, start + len(marker)) >= 0:
                raise ValueError(f"Missing or duplicate writing reference anchor {name}#{anchor}")
            end = content.find('<a id="', start + len(marker))
            selected.append(content[start:end if end >= 0 else len(content)].strip())
        content = "\n\n".join(selected) + "\n"
    selection = f" Selected criteria: {', '.join(anchors)}." if anchors is not None else ""
    return (f"\nAssigned writing method source: {path}.{selection} Resolve its links relative to "
            f"{path.parent}.\n" + content)


def load_role(role: str, writing: dict | None = None) -> str:
    if role not in {"coordinator", "literature", "simulation", "mechanism", "writer", "reviewer"}:
        raise ValueError(f"Unknown role {role}")
    root = resource_root()
    path = root / "roles" / f"{role}.md"
    if not path.is_file():
        raise ValueError(f"Missing role charter {role}")
    content = path.read_text(encoding="utf-8")
    for skill in selected_skills(role, writing):
        content += skill_text(skill, root, compact_section=True)
    for name in selected_references(role, writing):
        anchors = (section_reference_anchors(writing) if name == SECTION_REFERENCE else
                   distillation_reference_anchors(writing) if name == DISTILLATION_REFERENCE else
                   library_reference_anchors(writing) if name == LIBRARY_REFERENCE else
                   example_reference_anchors(writing) if name == EXAMPLE_REFERENCE else
                   source_example_reference_anchors(writing) if name == SOURCE_EXAMPLE_REFERENCE else None)
        content += reference_text(name, root, anchors=anchors)
    if writing is not None:
        scope = writing_selection(writing)
        content += f"\nAssigned writing mode: {scope['mode']}; sections: {', '.join(scope['sections'])}. "
        content += "Write only these sections; request needed supplementary evidence within the authorized research scope and await actual results. Do not invent findings or silently expand the study.\n"
        if role == "literature":
            content += "For source synthesis and citation verification, read the scientific-writing reference source-use.md.\n"
    return content
