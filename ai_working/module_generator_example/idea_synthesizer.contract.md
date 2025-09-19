# Module Contract: Idea Synthesizer

## Purpose
Generate net-new cross-document ideas from previously saved summary artifacts while maintaining explicit provenance and deterministic outputs.

## Inputs
- `summaries_dir` (Path, required): Directory containing `*.summary.json` files.
- `limit` (int, optional): Cap the number of summaries evaluated. Default: all.
- `filters` (list[str], optional): Glob patterns to include/exclude specific summary filenames.
- `params` (SynthesisParams, optional): Tunables controlling novelty thresholds and result counts.

### SynthesisParams
- `max_ideas` (int, default 10)
- `min_sources_per_idea` (int, default 2)
- `novelty_threshold` (float 0–1, default 0.6)
- `seed` (int | None)
- `sdk_timeout_s` (int, default 120)

## Outputs
- `IdeaRecord[]` returned in memory.
- Per-idea JSON artifact: `out/ideas/{idea_id}.json`.
- Append-only index: `out/ideas/index.jsonl`.
- Markdown brief for each idea: `out/ideas/{idea_id}.md` (human readable synopsis + provenance table).
- Metrics file: `logs/idea_synthesizer/{run_id}.metrics.json` summarizing tokens, latency, retries.

## Data Contracts

### SummaryRecord (input file schema)
- `digest` (str, sha256)
- `path` (str)
- `title` (str)
- `summary` (str, ≤400 words)
- `key_points` (list[str])
- `created_at` (RFC3339)

### IdeaRecord (output schema)
- `id` (str): `sha1(slug(title) + "|" + sorted(digests))`
- `title` (str, ≤100 chars)
- `rationale` (str): Explanation of novelty.
- `summary` (str): 1–3 paragraph description.
- `novelty_score` (float 0–1)
- `impact_score` (float 0–1)
- `effort_score` (float 0–1)
- `priority` ("high" | "medium" | "low")
- `sources` (list[{`digest`, `path`}])
- `constraints` (str | None)
- `created_at` (RFC3339)
- `source_manifest_hash` (str): Hash of all summary digests considered.

## Invariants
- Every idea references ≥2 distinct source digests.
- Outputs are deterministic given identical inputs and params (ordering seeded).
- Writes are atomic (temp file + rename) to preserve idempotency on resume.
- Markdown briefs mirror the JSON data and include a provenance table.

## Error Handling
- Missing or malformed summaries raise `SummaryLoadError`.
- Claude Code SDK timeouts trigger retry (up to 2 attempts) then surface `IdeaSynthesisTimeout` with partial telemetry saved.
- Schema validation failures abort the run and record diagnostics in metrics file.

## Usage Example
```python
from idea_synthesizer import IdeaSynthesizer, SynthesisParams

synth = IdeaSynthesizer()
ideas = synth.run(
    summaries_dir=Path("tmp/summaries"),
    params=SynthesisParams(max_ideas=5, seed=42)
)
```

## Non-goals
- No embedding storage or vector search.
- No direct modification of source summaries.
- No UI beyond generated files.
