---
module: idea_synthesizer
artifact: spec
contract_ref:
  module: idea_synthesizer
  version: "1.0.0"
targets:
  - python>=3.11
level: high
---

# Idea Synthesizer — Implementation Spec

## Implementation Overview
Implement the idea synthesizer as a pipeline of five regenerable bricks: summary loader, context partitioner, synthesis engine, persistence manager, and orchestrator/CLI. Each brick follows its own contract/spec pair. The orchestrator imports dependency **functions** exactly as published by their contracts (no private classes). After generation the tool must emit a top-level README and a runnable sample script that exercises the pipeline end-to-end; the module generator will execute that script automatically.

## Core Requirements Traceability
- Contract §Public API → `orchestrator/orchestrator.py::SynthesisOrchestrator.synthesize`, `__init__.py::synthesize_ideas` wrapper, and `cli/main.py` entrypoint.
- Contract §Data Models → `orchestrator/models.py` for request/response structures.
- Contract §Error Model → orchestrator exception translation + CLI exit codes.
- Contract §Conformance Criteria → unit tests in each brick, CLI tests, and sample-script smoke test.
- Contract §Metrics → `synthesis_engine/metrics.py` and orchestrator aggregation.

## Internal Design & Data Flow
1. **Summary Loader (`summary_loader`)** — synchronous discovery + parsing + manifest hash computation; exposes `load_summaries()` returning `SummaryCollection`.
2. **Context Partitioner (`context_partitioner`)** — token-aware greedy batching with overlap metadata; exposes `partition_summaries()` and `estimate_tokens()`.
3. **Synthesis Engine (`synthesis_engine`)** — deterministic heuristic idea generation; exposes module-level `synthesize_ideas(partition, config)` returning `(ideas, metrics)`.
4. **Persistence Manager (`persistence_manager`)** — atomic file writes, manifest/idempotency helpers, index maintenance; exposes `write_idea`, `write_manifest`, `check_manifest`, `update_index`, `get_existing_ideas`.
5. **Orchestrator (`orchestrator`)** — async coordination that imports the functions above directly; aggregates metrics, logs, error codes.
6. **CLI** — Thin Click wrapper invoking `synthesize_ideas`; supports config file, JSON/table output, and verbose logging.
7. **Sample Script** — `scripts/run_idea_synth_sample.py` loads fixtures from `ai_working/idea_synthesizer/sample_summaries/` and prints JSON or human-friendly output. Generator must run this script post-build; failures trigger regeneration attempts with captured logs.

## Dependency Usage (within orchestrator)
- All dependency interactions must go through published module functions (no hidden classes). When async coordination is required, wrap synchronous functions with `asyncio.to_thread`.
- The orchestrator is the only brick aware of all others; lower bricks remain isolated per their contracts.

## Logging
- Each brick defines its own logger (`amplifier.idea_synthesizer.<brick>`).
- Orchestrator logs start/end of runs, partition counts, persistence results.
- CLI logs user-visible progress in verbose mode.
- Sample script writes concise stdout plus optional JSON.

## Error Handling
- Each brick raises its contract-specific errors; orchestrator catches and maps them to `SYNTH_*` codes.
- `synthesize_ideas()` wrapper surfaces `SynthesisError` subclasses for synchronous callers.
- CLI maps orchestrator errors to exit codes: config=1, runtime=2, filesystem=3.
- Sample script exits non-zero on failure to support automated verification.

## Configuration
- Consumer-visible knobs documented in individual contracts.
- Internal env vars: `IDEA_SYNTH_CONCURRENT_PARTITIONS`, `IDEA_SYNTH_MAX_PARTITION_SIZE`, `SYNTH_ENGINE_*` overrides as described in respective specs.

## Output Files
- `amplifier/idea_synthesizer/README.md` — overview, brick map, quick-start instructions.
- `amplifier/idea_synthesizer/__init__.py` — public API wrapper + error re-exports.
- Brick directories with implementations + tests:
  - `summary_loader/`
  - `context_partitioner/`
  - `synthesis_engine/`
  - `persistence_manager/`
  - `orchestrator/`
  - `cli/`
- `scripts/run_idea_synth_sample.py` — sample runner invoked by generator smoke test.
- Integration tests (if needed) under `amplifier/idea_synthesizer/tests/`.
- Update or create plan artifacts under `ai_working/idea_synthesizer/` as necessary (handled by generator).

## Test Plan & Scaffolding
- **Unit tests**: Provided per brick (loader, partitioner, synthesis engine, persistence, orchestrator, CLI) using deterministic fixtures.
- **Sample runner**: script returns success exit code when pipeline completes; generator treats failure as generation error and triggers retry with captured output.
- **Manual verification**: README instructs developers to run the sample script and inspect `tmp/idea_synth_output`.

## Risks & Open Questions
- Deterministic synthesis logic remains heuristic; future LLM integration requires updating contracts.
- Token estimation fallbacks may differ from production tiktoken accuracy; monitor once we have integration tests.
- Persistence strategy writes many files; consider optional batch export in later revisions.
