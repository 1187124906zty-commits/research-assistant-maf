# MAF execution and operational boundaries

The Microsoft Agent Framework carrier organizes model calls, bounded assignments and collection of results. Scientific state is the project's recorded question, claims, evidence and dispositions; execution records describe what was dispatched and returned. Conversation history and workflow checkpoints are not a second scientific authority.

Use the project's current command help and setup documentation for supported providers, prerequisites and options. Skill discovery does not install a solver, grant access to data, create a license or make a referenced service available.

## Dispatch and return

Register a valid assignment before dispatch. Include its task context, original evidence locators and owned outputs. Use fresh bounded worker context rather than inheriting the leader's entire conversation. When the Codex provider uses a fresh thread per assignment, this separation does not imply statistical independence or hard sandboxing.

Collect actual artifacts and the contribution-bearing return. Apply shared-state changes through the designated coordinator path; specialists write separate outputs. Protocol validation can check shape, paths and registered dependencies. It cannot establish scientific correctness, adequate numerical error or physical validation.

Cycle and concurrency limits control execution cost. They are not evidence thresholds. Reaching a limit requires a partial deliverable with unresolved questions, not a fabricated success. Preserve negative findings rather than retrying the same scientific hypothesis as though it were a transport error.

## Interrupted work

Do not automatically replay an in-flight assignment after interruption. Inspect execution records, external job/process identity and produced outputs. Reconcile a completed job, explicitly abandon an unusable assignment, or submit a new bounded task. Recovering a framework checkpoint does not guarantee exactly-once external execution or cancel an existing solver.

Before reusing restored context, check current claims and input bindings. A stale checkpoint cannot restore a conclusion invalidated by later evidence. Preserve the current scientific state and the interruption history.

## Coverage limits

Recorded attempts and explicit tool calls can be budgeted. Arbitrary shell/solver operations inside a worker are not automatically intercepted or metered by an outer framework. Expensive work should report actual runs and costs. Stronger submit/poll/cancel control requires a dedicated tool adapter.

Do not claim all-software integration, hard enforcement or scientific validation from a successful MAF run. Distinguish model/provider failure, interrupted external work, inadequate evidence and a useful negative scientific result; they need different recovery actions.
