---
name: scientific-writing
description: Connect MAF writing assignments to the maintained research-writing-skill while preserving explicit task modes, section selection and standalone fallback.
---

# Scientific Writing Core

MAF uses the installed `research-writing-skill` as its writing entry. The role loader reads that entry once and keeps the existing `task.writing` mode and section selection. Its writing criteria and selected workflow belong to that maintained skill; this adapter does not reproduce them.

The default location is `$CODEX_HOME/skills/research-writing-skill/SKILL.md`, or `~/.codex/skills/research-writing-skill/SKILL.md` when CODEX_HOME is unset. `MAF_RESEARCH_WRITING_SKILL` may name an explicit entry file. A configured missing or misnamed entry is an error. The adapter does not install skills or change host settings.

For the scope handoff see [writing interface](references/scientific-story.md). Source-library format details remain in [library adapter](references/library-adapter.md).

When no implicit host entry is available, the loader retains MAF's [bundled writing core](references/legacy-writing-core.md) and existing chapter routes, source examples and review contracts for standalone operation. These fallback resources are not also injected with the maintained entry.
