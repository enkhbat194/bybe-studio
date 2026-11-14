# Optional MCP integration — planned, not active

BYBE Studio works without Codex, paid model tokens, REAPER's reper MCP or internet.

Possible tools:
- bybe_status: read local QA status
- bybe_list_clips(part, status): enumerate clips
- bybe_get_source_context(id, pad): get capped source audio context
- bybe_suggest_boundaries(id): proposal only, never overwrite
- bybe_run_asr(id, model): optional Qwen3/Whisper
- bybe_create_candidate(id, start, end): append immutable revision, reset QA
- bybe_submit_qa(id, checklist): only from actual user review
- bybe_backup: produce validated backup manifest

All file paths must be resolved from trusted source IDs; no arbitrary local file read or write by MCP tools. Bind only to loopback; no publicly exposed MCP. Add explicit write authorization, audit records, and tests. Never modify existing reper configuration.
