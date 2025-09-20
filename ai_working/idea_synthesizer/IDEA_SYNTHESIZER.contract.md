# Module Contract: Idea Synthesizer

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

## Data Contracts

### `IdeaRecord` (JSON schema shape)
- `id` (string, required): Stable slug (see ID rules).
- `title` (string, required)
- `summary` (string, required): 1–3 paragraphs.
- `rationale` (string, required): Why this idea is non-trivial and new vs. source content.
- `novelty_score` (0..1, required)
- `impact_score` (0..1, required)
- `effort_score` (0..1, required)
- `tags` (array<string>, optional)
- `provenance` (array of `{summary_path, summary_hash}`)
- `source_manifest_hash` (string, required)
- `created_at` (RFC3339, required)

### ID rules
- `idea-id = slugify(title) + "-" + short(content-hash)`

## Invariants / Acceptance Criteria
- **Net-new**, not a restatement of a single summary.
- Every idea lists ≥1 inspiration summary.
- **Atomic writes**; **Idempotent** for same inputs.
- Deterministic under fixed seeds.

## Errors
- `NoSummariesError`, `ParseError`, `WriteError`

## Dependencies
- Claude Code SDK for AI synthesis; subagents from `.claude/agents/`.
