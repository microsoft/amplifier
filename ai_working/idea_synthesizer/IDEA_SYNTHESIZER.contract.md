# Module: idea_synthesizer

## Purpose
Given a set of summary files produced upstream, synthesize **net-new** cross-document ideas, with clear provenance (which summaries inspired each idea), and persist them to disk as atomic, machine-readable artifacts.

## Inputs
- `summaries_dir` (path, required): Directory containing `*.summary.md`.
- `limit` (int, optional): Max number of summaries to consider; default: all.
- `filters` (optional): Include/exclude glob patterns for filenames.
- `run_id` (string, optional): Execution ID used for logs/traceability.

## Outputs (artifact-level)
- One file per idea: `ideas/<idea-id>.idea.json`
- Index file (append-only, idempotent): `ideas/_index.jsonl`
- Provenance map (optional): `ideas/_provenance.json`

## Observable Side-effects
- Structured progress logs: `logs/idea_synthesizer/<run-id>.jsonl`
- Metrics summary: `logs/idea_synthesizer/<run-id>.metrics.json`

## Data Contracts

### `IdeaRecord` (JSON schema shape)
- `id` (string, required): Stable slug (see ID rules).
- `title` (string, required)
- `summary` (string, required): 1–3 paragraphs.
- `rationale` (string, required): Why this idea is non-trivial and new vs. source content.
- `novelty_score` (0..1, required): Model-estimated novelty vs. provided summaries.
- `impact_score` (0..1, required): Estimated impact.
- `effort_score` (0..1, required): Estimated lift.
- `tags` (array<string>, optional)
- `provenance` (array of `{summary_path, summary_hash}`): Which summaries inspired it.
- `source_refs` (array<path>, optional): Direct pointers to original `.md` files, if derivable.
- `constraints` (string, optional): Noted risks/assumptions.
- `created_at` (RFC3339, required)
- `source_manifest_hash` (string, required): Hash of summary set considered.

### ID rules
- `idea-id = slugify(title) + "-" + short(content-hash)`
- Must be stable given the same summaries set; collisions append `-n`.

## Invariants / Acceptance Criteria
- **Net-new**: Must not just restate any single summary; cross‑summary synthesis is mandatory.
- **Explain provenance**: Every idea lists at least one inspiration summary.
- **Atomic writes**: No partial idea files.
- **Idempotent**: Re-running with unchanged inputs produces no new artifacts.
- **Determinism under fixed seeds**: With same inputs + fixed randomness, IDs and counts are stable.

## Errors
- `NoSummariesError` if zero usable summaries.
- `ParseError` if any summary cannot be read.
- `WriteError` on failed artifact writes (must leave no partials).

## Dependencies
- Claude Code SDK for AI synthesis. Use subagents to isolate synthesis context and parallelize chunks safely.
- Permissions come from `.claude/settings.json`; we **cannot** set tool rules programmatically—SDK reads them from settings.