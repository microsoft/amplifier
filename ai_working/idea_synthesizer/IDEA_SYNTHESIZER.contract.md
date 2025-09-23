---
module: idea_synthesizer
artifact: contract
version: 1.0.0
status: beta
---

# Idea Synthesizer — Contract

## Role & Purpose
Coordinate the end-to-end pipeline that turns a directory of upstream `*.summary.md` files into persisted, net-new ideas with provenance, summary statistics, and metrics suitable for downstream tooling. Consumers call this module to synthesize ideas exactly once per input manifest and rely on idempotent persistence.

## Public API
### synthesize(config: SynthesisRequest) -> SynthesisResponse

**Parameters**
- `summaries_dir` (`Path`, required): absolute or cwd-relative directory containing upstream summary files.
- `output_dir` (`Path`, required): directory used to write generated ideas and manifest metadata; will be created if missing.
- `limit` (`int`, optional): maximum number of summaries to load; default `None` (all).
- `include` (`list[str]`, optional): glob patterns; only matching files are considered.
- `exclude` (`list[str]`, optional): glob patterns to remove from the candidate set.
- `run_id` (`str`, optional): caller-supplied correlation id used in logs/metrics; default auto-generated.

**Returns**
- `SynthesisResponse` (see Data Models) describing counts, manifest hash, total cost, latency metrics, and provenance mapping.

**Semantics**
- **Preconditions:** `summaries_dir` must exist and be readable; `output_dir` must be writable.
- **Postconditions:**
  - All loaded summaries are recorded in a deterministic `source_manifest_hash` (sha256 of ordered `(path, hash)` pairs).
  - Generated idea documents (`*.idea.json`) and index entries exist in `output_dir` when ideas are produced.
  - Idempotency: if `output_dir` already contains a manifest matching the computed hash, no new ideas are written and the response reports zero generated ideas.
- **Invariants:**
  - No partial persistence: either all new ideas for the run are written atomically or none are.
  - Every generated idea records at least one provenance entry referencing input summaries.
  - Errors encountered while loading or synthesizing are surfaced without leaving transient files.

## Data Models

```json
{
  "SynthesisRequest": {
    "summaries_dir": "<path>",
    "output_dir": "<path>",
    "limit": "int | null",
    "include": "string[]",
    "exclude": "string[]",
    "run_id": "string | null"
  },
  "SynthesisResponse": {
    "run_id": "string",
    "summaries_total": "int",
    "summaries_processed": "int",
    "ideas_generated": "int",
    "ideas_skipped": "int",
    "ideas_dir": "string",
    "source_manifest_hash": "string (hex)",
    "session_metrics": {
      "total_cost": "float (USD)",
      "input_tokens": "int",
      "output_tokens": "int",
      "api_calls": "int",
      "latency_ms": "int"
    },
    "provenance_map": {
      "<idea_id>": ["<summary_path>"]
    },
    "processing_time_s": "float"
  }
}
```

## Error Model
- `SYNTH_LOAD_ERROR` — failure to read summaries directory (missing permissions, IO error); no files written; retry after fixing IO issue.
- `SYNTH_NO_SUMMARIES` — no summaries matched include/exclude filters; no files written; retry once summaries exist.
- `SYNTH_CONFIG_ERROR` — invalid request values (negative limit, invalid patterns); fix and retry.
- `SYNTH_RUNTIME_ERROR` — unexpected runtime failure; may be retried after investigation (idempotent).
- `SYNTH_IDEMPOTENT_SKIP` — reported when manifest already processed; informational only.

## Performance & Resource Expectations
- Designed for up to ~200 summaries per invocation; larger sets should be chunked upstream.
- Typical latency: < 30s for 100 summaries when using local deterministic synthesizer.
- All filesystem writes happen under `output_dir`; no network calls are required for the deterministic implementation.

## Configuration (Consumer-Visible)
- **IDEA_SYNTH_MAX_SUMMARIES** — Optional int; upper bound on summaries processed per run; defaults to unlimited (uses `limit` when provided).
- **IDEA_SYNTH_ENABLE_VERBOSE_METRICS** — Optional bool; when truthy, emits detailed metrics logs.

## Conformance Criteria
- Given missing `summaries_dir`, raise `SYNTH_LOAD_ERROR` and leave `output_dir` untouched.
- Given an existing manifest with identical hash, return `SYNTH_IDEMPOTENT_SKIP` semantics and do not write new idea files.
- Every generated idea must reference at least one source summary in the provenance map.
- Response `ideas_generated` equals the number of `.idea.json` files written during the invocation.

## Compatibility & Versioning
- Contract follows SemVer. Backward-compatible additions (new optional fields in `SynthesisResponse`) increment MINOR. Breaking changes to API, semantics, or error names require a MAJOR version bump.
- Deprecated fields remain for at least one MAJOR version with documentation in Usage Examples.

## Usage Example (Non-Normative)

```python
from pathlib import Path
from amplifier.idea_synthesizer import synthesize_ideas, SynthesisRequest

request = {
    "summaries_dir": Path("./summaries"),
    "output_dir": Path("./ideas"),
    "limit": 50,
    "include": ["*.summary.md"],
    "exclude": ["draft-*.summary.md"],
    "run_id": "marketing-q2"
}

response = synthesize_ideas(request)
print(response["ideas_generated"], "ideas saved to", response["ideas_dir"])
```
