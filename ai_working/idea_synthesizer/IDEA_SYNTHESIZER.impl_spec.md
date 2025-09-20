# Implementation Requirements: Idea Synthesizer

## Design Overview
Three steps: load → partition → synthesize.

1) Load summaries and compute a content-stable `source_manifest_hash` (ordered list of `(path, sha256)`).
2) Partition large sets; per partition, compact context (title + key points + brief).
3) Ask AI for candidate ideas with provenance; dedupe; persist atomically.

Use **subagents** (e.g., `idea-synthesizer`) to keep context isolated and parallelizable. Subagents are Markdown files under `.claude/agents/` and auto-detected by the SDK.

## SDK Usage
- Planning: read-only tools (`Read`, `Grep`), no writes.
- Generation: `acceptEdits` with `Write/Edit/MultiEdit/Bash` enabled.
- `cwd` = repo root; `add_dirs` includes `ai_context` and `amplifier`.
- Capture session ID, cost, and latency.

## Determinism & Dedupe
- Stable seed & sorted inputs.
- Fingerprint ID: `slug(title) + short_hash(sorted(provenance))`.

## Resume/Idempotency
- Skip writing if idea file exists with matching `source_manifest_hash`.
- Append missing entries to `_index.jsonl` if needed.

## Observability
- Emit simple metrics (counts, latency).

## Quality Bar
- ≥ K ideas (configurable) with provenance.
- Zero schema violations.
- Re-run with same inputs + seed yields identical IDs.
