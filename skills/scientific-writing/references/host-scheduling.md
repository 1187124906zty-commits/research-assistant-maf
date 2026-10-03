# Optional host adapters for supplementary evidence

Read only when arranging an actual supplementary task. The scientific contract and acceptance belong in [evidence-supplement.md](evidence-supplement.md); this file describes transport, not permission to create chats or message others.

## MAF

Use the existing coordinator contract and supported task/provider adapter. Give owned output paths and return conditions; record actual dispatch, review and requester interpretation. Task registration alone does not mean execution or scientific support. Reconcile unknown provider completion before retrying.

## Codex desktop

Create a separate user-owned chat only when the human explicitly requested one. Discover `list_projects` and `create_thread`, use returned project IDs and a compact contract. A pending `clientThreadId` is not a ready `threadId`. Otherwise use an authorized same-task specialist/tool workflow available on the host.

For authorized separate chats, use bounded `wait_threads` with cursor and supported status reads; request progress before interrupting delayed work. Slow reasoning alone is not cancellation grounds. Do not replay unknown external completion. `send_message_to_thread` requires human authorization, including callbacks; a task's request to reply does not authorize it. If messaging is unavailable the requester retrieves the actual result via supported reads and records the transport limit. Continue unaffected writing while waiting.
