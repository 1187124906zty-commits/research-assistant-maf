---
name: simulation-evidence
description: Produce and assess simulation evidence for one bounded physics or engineering question, with faithful software mapping, claim-specific numerical checks, uncertainty and contribution-bearing returns.
---

# Simulation Evidence

Own the model-to-software mapping, actual simulation outputs and domain assessment for the assigned question. Explain what the evidence permits and what remains uncertain. The coordinator owns project priorities and contribution; do not create a second whole-project workflow or decide journal acceptance.

Under a coordinator, reuse its question, purpose, inputs, ownership, budget and return condition; add only necessary physics and numerical detail. When used alone, establish these in a short run plan. Inspect available files and software before asking the user to supply information that can be found locally.

## Prepare a fit-for-purpose run

State the stage, claim and intended use; define quantities of interest (QoIs), conditions, expected decision/effect scale and relevant uncertainty. Match fidelity to the question. A feasibility pilot, a resolved comparison and physical validation require different evidence. Read [adequacy-and-return.md](references/adequacy-and-return.md) for this distinction and the return protocol.

Close equations, units, material parameters and essential initial/boundary/interface conditions. Label inputs as confirmed, source-backed, software-default, calibrated, proposed, derived or unknown. A declared hypothetical model may use explicit assumptions but cannot impersonate a real experiment.

Prefer an available framework that expresses the chosen physics; custom methods are appropriate when requested or needed for a documented limitation. Check the actual software formulation or derive the discrete mapping where necessary. Explain capability gaps before expensive work.

Freeze inputs for a reproducible run, not the evolving research idea. Preserve run/input versions, environment and actual output paths. Use hashes when binary identity, concurrency, caching or the adapter requires them, rather than replacing scientific checks with repeated text checksums.

## Execute, assess and return

Run cheap consequential unit, sign, limit and closure checks and a relevant baseline before costly computation. Preserve raw outputs. Assess errors, balances and stability only as needed for the current QoI and claims, with reasons for omitted/nonapplicable checks.

Explain numerical variation relative to the claimed effect, input uncertainty and intended use. A small residual, plausible contour or zero exit code establishes neither a resolved comparison nor physical validity. Independent real-world referents are required for claims of physical validation; keep calibration and held-out validation separate.

Return the answer, actual evidence, checks, specialist adequacy rationale, uncertainty, negative findings, affected claims, costs and one useful next option. Explain what changed for the task's purpose. Distinguish execution, numerical verification, physical validation and mechanism interpretation; do not self-declare unique mechanism or broad transfer from a plot.

After two repair/refinement attempts without changed research understanding, or earlier budget exhaustion, return for coordinator reassessment. Propose a cheaper distinguishing test, a revised model/question or a narrower claim. Budget exhaustion cannot grant PASS. Once the question is answered, return without using the remaining budget for extra precision.

Classify failure before repairing: specification, physics, implementation, environment, numerics, comparison or provenance. Fix the responsible artifact and rerun affected checks. Important unresolved failures block their named claims; unaffected evidence remains useful. Do not erase failed checks through backend switching or retrospective tolerance changes.

Write assigned run/result files only. Challenge an infeasible or ill-posed task with evidence and an alternative; request an amended contract before changing physical scope or consequential validation criteria. Use bounded domain or independent review when consequential claims need it, rather than adding a review team to every pilot.
