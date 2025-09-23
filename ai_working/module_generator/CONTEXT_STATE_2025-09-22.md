# Idea Synthesizer Generator Context — 2025-09-22

## 1. High-Level Goal
Transform the `amplifier/tools/module_generator` into a reliable module builder that:
- Uses the new `amplifier/ccsdk_toolkit` for all Claude Code SDK interactions (streaming output, deterministic retries, progress visibility).
- Decomposes the Idea Synthesizer specification into modular bricks (`summary_loader`, `context_partitioner`, `synthesis_engine`, `persistence_manager`, `orchestrator`, `cli`, `sample_runner`) and regenerates code/test assets consistent with their contracts.
- Verifies the generated module end-to-end via an emitted sample script (`scripts/run_idea_synth_sample.py`) that exercises the pipeline against fixtures in `ai_working/idea_synthesizer/sample_summaries`.

## 2. What Already Works (2025-09-22)
### CCSDK Toolkit Alignment
- `SessionOptions` and `ClaudeSession` now accept cwd/add_dirs/tool permissions, progress callbacks, and streaming output. They honour `AMPLIFIER_CLAUDE_PLAN_TIMEOUT` (default 240 s) and `AMPLIFIER_CLAUDE_GENERATE_TIMEOUT` (default 3600 s, capped at 7200 s) so long-running generator runs show continuous progress.
- Planner/executor calls go through CCSDK toolkit wrappers. Prompts automatically include:
  - `@ai_context/MODULAR_DESIGN_PHILOSOPHY.md`
  - `@ai_context/module_generator/CONTRACT_SPEC_AUTHORING_GUIDE.md`
  - `@ai_context/AMPLIFIER_CLAUDE_CODE_LEVERAGE.md`
  - CCSDK developer guide (`@amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md`)
- `sdk_client.generate_from_specs()` streams Claude output, retries once with failure context if JSON parsing fails, and surfaces session metadata (session id, cost, duration). `executor/smoke.py` now runs the generated `scripts/run_idea_synth_sample.py` to ensure the pipeline works before reporting success.

### Idea Synthesizer Regeneration
- Refreshed top-level contract/spec (`ai_working/idea_synthesizer/IDEA_SYNTHESIZER.*`) and tracked fixtures (`sample_summaries/*.summary.md`).
- Orchestrator improvements:
  - Converts loader `SummaryCollection` into context partitioner models, wrapping them in `PartitionConfig` with the orchestrator’s env overrides (`ORCH_MAX_PARTITION_TOKENS`, defaults to 8000).
  - Converts partitioner output into synthesis engine `SummaryPartition` objects, constructing `SynthesisConfig` with deterministic seeds and quality thresholds (`ORCH_QUALITY_THRESHOLD`, default lowered to 0.3 to ensure ideas exist for sample fixtures).
  - Serialises idea dataclasses, writes atomic idea files, updates index, and writes manifest files (`manifest_<hash>.json`).
  - Checks manifest idempotency before heavy work; returns `ideas_skipped` equal to existing idea count if manifest already processed.
- `scripts/run_idea_synth_sample.py` now:
  - Adds repo root to `sys.path` so it runs from anywhere.
  - Loads fixtures from `SAMPLE_FIXTURES_DIR` (default `ai_working/idea_synthesizer/sample_summaries`).
  - Validates ideas/provenance/manifests and prints summary/table/json formats.
  - Accepts `--clean` to wipe output directory before execution.
- Full regeneration with streaming feedback completes: `AMPLIFIER_CLAUDE_PLAN_TIMEOUT=240 AMPLIFIER_CLAUDE_GENERATE_TIMEOUT=3600 .venv/bin/python -m amplifier.tools.module_generator generate ... --refresh-plan --force` (runtime ≈60 min, progress visible).

### Spec Generation Hardening
- `decomposer/specs.py` now parses Claude responses with the CCSDK defensive parser, and if parsing fails it retries up to three times with explicit “JSON only” guidance. This addresses cases where Claude embeds commentary above the JSON block.

## 3. Repository Snapshot (Post-Run)
- **Tracked**: refreshed top-level Idea Synthesizer contract/spec + fixtures. `scripts/run_idea_synth_sample.py` and modified toolkit/generator files are staged.
- **Untracked** (intentional): generated module directories under `amplifier/idea_synthesizer/` and `scripts/` subfolders (`scripts/tests/`, etc.). Decide whether to commit these or leave regeneration-only.
- `tmp/idea_synth_output/` is created only during validation runs (cleaned via `--clean`). `.claude/` directories contain Claude CLI cache/state—ignore or clean as desired.
- `pyproject.toml` / `uv.lock` match `origin/main`; no new runtime dependencies were committed.
- The branch still diverges from `origin/generator-from-code-cdx`; plan accordingly before committing large generated trees.

## 4. Outstanding Tasks / Follow-ups
1. Decide whether to commit the generated Idea Synthesizer module (all brick directories + sample script) or keep regeneration as a local step.
2. Revisit synthesis heuristics once the generator is stable—current `ORCH_QUALITY_THRESHOLD=0.3` guarantees sample success but may permit lower-quality ideas in other datasets.
3. Curate/commit brick-level tests if you want regression coverage (tests currently live in generated directories but are unstaged).
4. Update `.gitignore` if you want to suppress `.claude/` state directories or generated artifacts.
5. Consider capturing golden outputs for the sample runner (JSON export) to compare during future validations.
6. If new bricks (e.g., documentation/module root) are introduced, update plan templates and ensure `ensure_brick_specs()` still converges.
7. Hauskeeping: update branch with `origin/main` before committing to avoid manual conflict resolution later.

## 5. Reproducing Key Outcomes
```bash
# (Optional) capture generator output to a file
mkdir -p _tmp
AMPLIFIER_CLAUDE_PLAN_TIMEOUT=240 \
AMPLIFIER_CLAUDE_GENERATE_TIMEOUT=3600 \
  .venv/bin/python -m amplifier.tools.module_generator generate \
  ai_working/idea_synthesizer/IDEA_SYNTHESIZER.contract.md \
  ai_working/idea_synthesizer/IDEA_SYNTHESIZER.impl_spec.md \
  --refresh-plan --force \
  > _tmp/module_generator_run.log 2>&1

# Validate pipeline end-to-end (fixtures ➜ ideas ➜ manifest)
SAMPLE_FIXTURES_DIR=ai_working/idea_synthesizer/sample_summaries \
SAMPLE_TIMEOUT_S=600 \
  .venv/bin/python scripts/run_idea_synth_sample.py \
  --output-dir tmp/idea_synth_output --format summary --clean
```
Expect “Validation: ✓ All checks passed”. If validation fails, inspect the generated files in `tmp/idea_synth_output/` and log output to identify regressions (provenance missing, manifeset invalid, etc.).

## 6. Quick Checklist for Future Sessions
- `ai_working/module_generator/BOOTSTRAP_INSTRUCTIONS.md` (entry point).
- This file for global context.
- Strategic docs:
  - `@ai_working/ccsdk-amplifier-improvement-plan.md`
  - `@ai_working/ccsdk-toolkit-comprehensive-analysis.md`
- Generated artifacts:
  - `scripts/run_idea_synth_sample.py`
  - `amplifier/idea_synthesizer/orchestrator/orchestrator.py`
  - `amplifier/idea_synthesizer/synthesis_engine/synthesis.py`
  - `amplifier/idea_synthesizer/persistence_manager/persistence.py`
- Planning artifacts:
  - `ai_working/module_generator/plans/idea_synthesizer.plan.json`
  - `_tmp/module_generator_run.log` (if available) for long-run diagnostics.

## 7. Key Implementation Notes
- The orchestrator conversions (`_convert_to_partition_collection`, `_to_synthesis_partition`, `_serialize_idea`) are pivotal—any contract adjustments must update these helpers.
- Partitioning relies on the greedy algorithm with optional overlap; ensure `PartitionConfig` defaults remain in sync with orchestrator defaults.
- The sample runner only validates high-level invariants. For deeper coverage, add targeted tests per brick.
- Manifest and idea files now mirror production semantics (`ideas/*.idea.json`, `manifest_<hash>.json`, `ideas_index.json`). The validator expects this layout.
- Spec retry logic currently retries twice after the initial attempt. If Claude keeps appending commentary beyond three attempts, consider piping through a format-enforcing tool or tightening guidance further.

## 8. Environment Variables / Defaults
| Variable                               | Default | Purpose |
|----------------------------------------|---------|---------|
| `AMPLIFIER_CLAUDE_PLAN_TIMEOUT`        | 240     | Plan call timeout (seconds) |
| `AMPLIFIER_CLAUDE_GENERATE_TIMEOUT`    | 3600    | Generate call timeout (seconds, capped at 7200) |
| `ORCH_MAX_PARTITION_TOKENS`            | 8000    | Max tokens per partition |
| `ORCH_CONCURRENT_PARTITIONS`           | 3       | Async semaphore for partition processing |
| `ORCH_QUALITY_THRESHOLD`               | 0.3     | Minimum idea quality (lowered to ensure sample ideas) |
| `ORCH_SYNTHESIS_MODE`                  | `hybrid`| Synthesis engine mode (creative/analytical/hybrid) |
| `SUMMARY_LOADER_MAX_FILE_SIZE`         | 1 MB    | Skip larger fixtures during loading |
| `SAMPLE_FIXTURES_DIR`                  | `ai_working/idea_synthesizer/sample_summaries` | Fixture location for sample script |
| `SAMPLE_TIMEOUT_S`                     | 300     | Validation timeout (seconds) |

## 9. Repository Cleanliness Snapshot
- Untracked directories produced by regeneration: `amplifier/idea_synthesizer/`, `scripts/tests/`, `scripts/scripts/`, `amplifier/idea_synthesizer/{cli,context_partitioner,persistence_manager,summary_loader,synthesis_engine,orchestrator}/`. Remove or commit as desired.
- `.claude/` contains CLI cache/config; delete if you want to reset Claude CLI state.
- `tmp/idea_synth_output/` is safe to remove after validation runs.
