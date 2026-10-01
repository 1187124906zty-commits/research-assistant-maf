# AMMT manuscript assistance: actual MAF/Codex run

[Read the article PDF](https://github.com/1187124906zty-commits/research-workflow/blob/codex/researchflow-release/paper/ammt-study/manuscript.pdf) · [LaTeX and evidence package](https://github.com/1187124906zty-commits/research-workflow/tree/codex/researchflow-release/paper/ammt-study) · [Actual run summary](run-summary.json)

This case used the native MAF coordinator–parallel workers–collector graph and the real local `CodexProvider`. It is not the deterministic `demo` command. The original AMMT IN625 calculations came from SimAgent; the present session produced two bounded manuscript inputs from frozen evidence, without rerunning a PDE.

The mechanism worker delivered [mechanism-analysis.md](outputs/mechanism-analysis.md). The writer delivered [results-discussion.md](outputs/results-discussion.md). They began in parallel with separate outputs and fresh model context. Each return received a separate evidence review and requester disposition. The writer review found a speed-only attribution across A/B/C; the second bounded attempt restricted it to fixed-power B/C. The final article was assembled and independently reviewed by the parent ResearchFlow task.

## What the run establishes

- Actual model-backed role execution, file returns, independent review and requester interpretation on existing scientific material.
- Evidence-aware scope: B length calibration, nonblind comparisons, distinct observation populations, major tail sensitivity and unresolved fine contrasts.
- A concrete review contribution: conductivity changes both bulk diffusion and surface reconstruction; the final Discussion avoids exclusive bulk-transport attribution.
- A concrete correction: A/B change power and speed together, so only B/C support the fixed-power speed interpretation.

It does not establish scientific productivity gains, physical validation or universal autonomous completion. No manuscript artifact was promoted as physical evidence.

## Preserved interruption and recovery

The second writer repaired its sentence but returned line/JSON-fragment locators in a field that requires actual declared file paths. It also listed a session-only reviewer path. The runtime rejected evidence binding and stopped. The completed response and repaired file were inspected; root normalized the pointers to declared files and removed the non-file reviewer entry, preserving both [original](reconciliation-original.json) and [normalized](reconciliation-normalized.json) returns. The documented `reconcile` command imported the inspected result without rerunning the worker. The native graph then performed a further writing review, accepted the bounded result and completed.

This is an explicit recovery, not a hidden automatic retry. Reviews, return scopes, coordinator decisions and the completion statement are preserved under [reviews/](reviews/) and [returns/](returns/). Earlier review outputs are historical artifacts; the current writer file contains the repaired sentence. A historical stale-artifact warning can therefore remain nonblocking in the protocol audit after the task is closed.

The first mechanism reviewer inspected original evidence before producer interpretation and disclosed that it did not review the producer artifact. The writing reviewers read the actual section. Root read both worker outputs, and a separate manuscript reviewer inspected the complete article and rendered pages. These are distinct scopes.

## Run a new bounded session

Install the project's Codex extra, retain valid local Codex authentication, then run:

```powershell
python examples/ammt-manuscript/run_workflow.py --project ./workspaces/ammt-paper
```

This starts real model calls and consumes the configured account's resources. The script uses these frozen input copies and initializes disjoint mechanism/writer contracts. Outputs and runtime state go to the specified new project. It prepares manuscript inputs, not the entire journal article or a solver environment. Model choices, authentication and actual host permissions retain their configured defaults.

Frozen [inputs](inputs/) are prior extracted evidence rather than raw experimental data. Their original artifact locators may contain the development-machine path; resolve them through the linked SimAgent case when reopening originals. Publisher full-text papers, credentials and private app-server logs are not included.
