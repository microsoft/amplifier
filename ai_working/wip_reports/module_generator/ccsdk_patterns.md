# Claude Code SDK Patterns (WIP)

## Logging & Observability
- Log the first ~200 characters of system/user prompts.
- Normalize streamed messages into dicts via `_normalize_message`, emit human readable summaries (assistant text, tool uses, errors).
- Persist every message incrementally to `*.messages.jsonl` for post-run analysis and tailing during execution.

## Session Management
- Prefer turn caps (`max_turns`) over wall-clock timeouts; let the session run as long as Claude keeps responding.
- Reuse repo `.claude/settings.json` and pass `allowed_tools` explicitly per phase (plan vs generate).
- Provide CLI flags for `plan-max-turns`/`generate-max-turns` rather than hard-coding.

## Error Handling
- Detect `subtype == "error_max_turns"` messages and surface warnings; decide whether to retry with higher caps.
- Strip Markdown fences before JSON parsing; tolerate both array and single-object responses.
- Wrap attribution and validation failures in domain-specific exceptions (`IdeaSynthesisError`, `AttributionError`).

## Filesystem Practices
- Write plan/generation artifacts and usage stats to `ai_working/module_generator_runs/<module>/`.
- Use atomic write helpers (`atomic_write_text/json/jsonl`) with `asyncio.to_thread` when called from async contexts.

## Telemetry Hooks
- Provide timers (`start_timer`/`end_timer`), event recorder (`record`), token counters, and metrics snapshots for downstream logging.
- Persist metrics with timestamped filenames for audit.

## Testing Strategy
- Mock Claude SDK responses at the edge (`ClaudeIdeaSynthesizer.generate`) to keep tests deterministic.
- Include fixtures for summary inputs to validate chunking, resume semantics, and output formatting.

These patterns should be promoted into a reusable SDK toolkit or cookbook for future tooling.
