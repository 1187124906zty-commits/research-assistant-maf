# Bounded native MAF recovery diagnosis

This diagnosis reads the existing workspace and Codex public SDK thread history. It starts no model turn, does not repeat either writing task, does not alter runtime/skills/tests, and does not edit the canonical manuscript.

## Attainable status

The native MAF run remains `attention`, `cycles=0`. No native MAF reviewer or requester disposition has executed. Both scientific tasks remain `active` with zero imported attempts and zero decisions because the fork/join batch was interrupted before collection completed.

| Call | Ledger | Last persisted turn | Structured final response |
|---|---|---|---|
| `worker:R2_INTRODUCTION:1` | completed | completed | Recovered exactly and schema-validated; original ledger already holds it |
| `worker:R2_DISCUSSION:1` | failed ProviderError/deadline | interrupted | None matching the original RESULT schema |

The final discussion turn is persisted as `interrupted`. The diagnostic app-server reports its thread as `notLoaded`; it is not an active turn in this diagnostic process. This confirms the original parent worker turn was interrupted, without asserting termination of every external/child process. Session and turn locators remain in the private local ledger; this public diagnosis omits them.

## Actual files inspected

Discussion `r001` contains `draft.tex`, `argument.md` and `memory.md`. Discussion `r002` contains `draft.tex` and `argument.md`, but **no `r002/memory.md`** at diagnosis time.

The worker also wrote `reviews/science-r001.md`, `argument-r001.md`, `requester-dispositions-r001.md`, corresponding r002 reports, and `requester-dispositions-r002.md`. These are worker-internal review records, not native MAF `reviewer` calls or native shared-state dispositions. The r002 disposition names `r002/memory.md` among accepted files even though it is absent, so that stated three-file closure is incomplete.

The r002 draft is substantial scientific prose and its argument records limited editorial changes following the worker's section reviews. It remains a candidate available to root integration. Its existence does not establish a completed structured handoff or whole-paper review.

## Recovery decision

The existing `reconcile` interface accepts an inspected actual response matching the original call schema and binds its artifact versions. It does not authorize inventing a new final response for a call that has none. No original discussion structured response was found, so the exact-response reconciliation path cannot complete this native batch honestly.

Accordingly, this bounded diagnosis did not reconcile or resume the run, fabricate RESULT JSON, rerun the worker, or claim native review completed. Root subsequently received the existing candidate, conducted cross-section mechanism review, and integrated the manuscript for fresh whole-paper review. Those actual Codex research-team activities remain separate from the incomplete native MAF batch. Native recovery still requires an explicit source-bearing partial-output disposition or a narrowly scoped same-worker finalization operation, distinguished from replaying the chapter-writing task. The current code does not guarantee an automatic native closed loop.

## Artifacts

- `inspect_calls.py`: read-only public SDK history inspection and exact-response extraction.
- `call-diagnosis.json`: public status report and response availability, with session/turn identifiers and host absolute paths removed; no transcript or credential dump.
- Exact recovered Introduction final response: retained locally under an ignored `*-recovered.json` filename. Its host-specific locators are not published.

No discussion recovered-response file is written because no qualifying final response exists.

`inspect_calls.py` reads session locators from the local ledger and writes a sanitized public summary. It stores any exact response separately in the ignored local file and starts no model turn. A public clone does not contain the private run workspace or exact returned response; its absence is intentional and is not a missing public deliverable.
