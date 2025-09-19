# Implementation Spec: Idea Synthesizer

## Overview
Build a module `idea_synthesizer` that consumes summary artifacts and emits net-new ideas with provenance. The implementation must respect the contract, support resume semantics, and integrate with Claude Code SDK headless sessions.

## Dependencies
- Python 3.11+
- `pydantic` for schema validation.
- `aiofiles` or stdlib `asyncio` file APIs for atomic writes (use temp files + rename).
- `claude-code-sdk` Python package with Node.js CLI available in PATH.
- Internal utilities:
  - `amplifier.utils.files.atomic_write`
  - `amplifier.utils.hashing.digest_bytes`
  - `amplifier.utils.telemetry` (create if absent) for metrics aggregation.

## Key Components
1. **Models** (`models.py`)
   - `SummaryRecord`, `IdeaRecord`, `SynthesisParams` (Pydantic models with validation).
2. **Store** (`store.py`)
   - `SummaryStore`: Loads summaries from disk, filters, handles limit, and computes manifest hash.
   - `IdeaStore`: Writes JSON, index, and markdown files atomically. Maintains resume checks.
3. **Claude Integration** (`sdk.py`)
   - `ClaudeIdeaSynthesizer`: wraps `ClaudeSDKClient` with `ClaudeCodeOptions` configured for headless mode, `permission_mode="plan"` for evaluation and `"acceptEdits"` when writing todos.
   - Handles streaming responses, JSON parsing, markdown fence stripping, and captures todos/cost metrics (see `CLAUDE_CODE_SDK_TODO_TRACKING.md` and `CLAUDE_CODE_SDK_TRACKING_COST.md`).
   - Enforces 120 s timeout using `asyncio.timeout` and retries (max 2) with exponential backoff (1.5x).
4. **Engine** (`engine.py`)
   - `IdeaSynthesizer`: orchestrates load → batch → prompt → verify → persist.

## Algorithm
1. **Load summaries** via `SummaryStore.load()` producing `SummaryBatch` and `manifest_hash`.
2. **Normalize content**: strip whitespace, dedupe digests, truncate summaries to 400 words.
3. **Chunk**: group summaries into ≤10 items per Claude call to manage context.
4. **Prompt assembly**:
   - System prompt emphasizes novelty, provenance, JSON output (link to `PromptPacks`).
   - User message includes structured list of summaries (title, key points, snippet).
5. **Claude call**: `ClaudeIdeaSynthesizer.generate(batch, params)` returns parsed `IdeaRecord` objects.
6. **Novelty gating**: Optional secondary pass using subagent `novelty-auditor` (if available) to score novelty; drop items under threshold.
7. **Attribution verification**: Ensure cited digests exist in batch; raise if missing.
8. **Persist** using `IdeaStore` (atomic writes). Update index JSONL and metrics file.
9. **Telemetry**: capture tokens, duration, retries, and final counts; flush via `TelemetryRecorder`.

## Prompts
- Store under `prompts/idea_synthesizer/`. Provide `synthesize_ideas.system.md` and `synthesize_ideas.user.jinja` templates with placeholders for summaries and params.
- Include instructions to output raw JSON (no markdown fences) and to provide novelty score, rationale, and source digests.

## Error Handling
- Wrap Claude operations in try/except to distinguish timeout vs parsing vs validation errors.
- Validation issues produce `IdeaValidationError` with context recorded in metrics file.
- On partial failure, continue with remaining batches, logging reasons.

## Testing Strategy
- Unit tests for model validation and store behaviors (skip/overwrite, atomic writes).
- Integration test with Claude layer mocked to return fixture JSON verifying full flow.
- Ensure deterministic IDs by asserting hashed output with fixed seed.

## Observability
- Log start/end of each batch with counts.
- Persist `metrics.json` containing: total summaries, total ideas, retries, max latency, tokens (input/output), SDK session UUID.
- Use SDK cost tracking hooks per `CLAUDE_CODE_SDK_TRACKING_COST.md` to gather cost data.

## Time & Resume Considerations
- Before generating new idea files, check `IdeaStore.exists(id)` and skip if present when `allow_overwrite` is False.
- Use `tempfile.NamedTemporaryFile(delete=False)` in same directory, then `os.replace` for atomic writes.
- Allow CLI to pass `--force` to override existing outputs by clearing directory first.

## Open Questions
- Do we need configurable output formats beyond JSON/Markdown? (Deferred)
- Should novelty auditing be required or optional based on subagent availability? (Default to optional with log warning when missing.)
