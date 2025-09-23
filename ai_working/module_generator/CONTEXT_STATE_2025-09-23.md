# Idea Synthesizer Generator Context — 2025-09-23

## 1. Mission Refresher
We are hardening the `amplifier/tools/module_generator` so it can, without human patch-ups, regenerate the Idea Synthesizer module as a collection of independently buildable bricks. Success now means:
- All Claude Code SDK usage flows through the new `amplifier/ccsdk_toolkit` streaming wrappers (no raw CLI calls, progress is visible, long jobs stay chatty).
- The decomposer emits contracts/specs per brick using the philosophy defined in `@ai_context/MODULAR_DESIGN_PHILOSOPHY.md` and `@ai_context/module_generator/CONTRACT_SPEC_AUTHORING_GUIDE.md`.
- The generator produces:
  1. Brick implementations + tests.
  2. A top-level package README summarising the regenerated module.
  3. A runnable validation script (currently `scripts/run_idea_synth_sample.py`).
  4. An automated smoke run of that script as part of the generation pipeline, failing fast if the artefacts do not work.
- All verification (sample script, CLI exercise) happens automatically inside the generator run.

## 2. What Changed Since 2025-09-22
- **New toolkit baseline:** The branch now includes the merged `amplifier/ccsdk_toolkit/` helpers (see `examples/` for streaming patterns). Planner/executor code paths call into these helpers; session options honour `AMPLIFIER_CLAUDE_PLAN_TIMEOUT` and `AMPLIFIER_CLAUDE_GENERATE_TIMEOUT`.
- **Fresh contracts/specs:** `ai_working/idea_synthesizer/IDEA_SYNTHESIZER.*` were regenerated. Additional brick contracts/specs live beside them (e.g. `summary_loader`, `context_partitioner`). These will be regenerated again once the generator is fixed; treat the current ones as disposable.
- **Sample runner script:** `scripts/run_idea_synth_sample.py` exists and adds the repo root to `sys.path`. It accepts `--format {summary,table,json}` and `--clean` and uses fixtures in `ai_working/idea_synthesizer/sample_summaries/`.
- **Generator wiring:** `executor/smoke.py` invokes the sample runner at the end of a successful generation.
- **Partial transcript archive:** A truncated copy of the conversation so far lives at `~/amplifier/transcripts/2025-09-23-amplifier-generator-from-code-cdx-partial.txt`. Use it if you need more narrative detail than these context files provide.

## 3. Current Blockers / Failures
1. **Sample runner import failure** — Running `uv run python scripts/run_idea_synth_sample.py` raises `ImportError: cannot import name 'ContextPartitioner'`. The orchestrator’s `default_components.py` expects `ContextPartitioner` to be exported from `amplifier.idea_synthesizer.context_partitioner.__init__`, but the generated brick does not re-export it. Fix this in the module generator (contracts/specs and generated code), *not* by hand-editing the brick.
2. **CLI binary missing** — `uv run idea-synth …` fails with “Failed to spawn”. The generator currently builds `amplifier.idea_synthesizer.cli` but never installs an entry point. Until we decide to package it, the supported invocation is `uv run python -m amplifier.idea_synthesizer.cli …`. The generator should either emit packaging metadata or update docs/sample script to use the module form.
3. **Spec JSON leakage** — `ensure_brick_specs()` still occasionally receives Claude responses with commentary above the JSON payload (seen when generating the `synthesis_engine` specs). Although the retry logic improved, we need a hardened guard that strips non-JSON prologues or repeatedly instructs Claude until a clean payload is produced.
4. **Auto-validation gap** — The generator currently stops after writing artefacts; it must *always* run the sample script (using the re-entrant smoke step) and only declare success if that script returns zero. If the script fails, the generator should capture stdout/stderr and retry after nudging Claude, mirroring how spec parsing retries work.

## 4. Immediate To-Do List (Generator Side)
1. Update decomposer/planner prompts so each brick contract/spec advertises the public exports the orchestrator expects (e.g. `__all__` contents). The context_partitioner brick must expose `ContextPartitioner`, `partition_summaries`, and related models.
2. Extend generator templates so the top-level package README and validation script are *explicit* outputs, not incidental side effects. Include acceptance checks that read those files back and verify required sections/flags.
3. Teach `executor/smoke.py` to stream progress (use `ccsdk_toolkit` progress callbacks) and, on failure, to send Claude the captured logs so it can attempt a fix.
4. Ensure prompts @mention the key philosophy docs (`@ai_context/MODULAR_DESIGN_PHILOSOPHY.md`, `@ai_context/module_generator/CONTRACT_SPEC_AUTHORING_GUIDE.md`, `@ai_context/IMPLEMENTATION_PHILOSOPHY.md`) and the new toolkit docs (`@amplifier/ccsdk_toolkit/DEVELOPER_GUIDE.md`, `@amplifier/ccsdk_toolkit/examples/streaming_status.md` if you add one) every time the SDK is invoked.
5. Merge the latest `origin/main` before continuing substantive work (this branch has diverged).
6. Update `.gitignore` if we intend to leave generated artefacts untracked (currently many brick directories show up as `??`).

## 5. Safety Rails / Operating Rules
- **Do not patch generated brick code directly.** All fixes must come from contracts/specs or generator logic, otherwise we break reproducibility.
- **Always validate via the sample script** before reporting success. Use `SAMPLE_FIXTURES_DIR=... .venv/bin/python scripts/run_idea_synth_sample.py --format summary --clean` locally if you need manual confirmation, but the ultimate goal is automation inside the generator.
- **Use specialised sub-agents.** The project provides `amplifier-cli-architect` (see `.claude/AGENTS_CATALOG.md`) for CCSDK/generator architecture questions; spin it up proactively when refining prompts or execution flow.
- **Stream feedback for long calls.** Claude sessions may run for close to an hour; progress hooks must emit periodic status so operators know the job is alive.

## 6. Files Worth Inspecting on Resume
- `@ai_working/module_generator/BOOTSTRAP_INSTRUCTIONS.md` (entry point, updated to reference this doc).
- `@ai_working/ccsdk-amplifier-improvement-plan.md` and `@ai_working/ccsdk-toolkit-comprehensive-analysis.md` for broader strategy.
- `@amplifier/tools/module_generator/ARCHITECTURE.md` (recently touched) to understand current flow.
- `@amplifier/ccsdk_toolkit/examples/` for streaming/progress implementation hints.
- `@ai_working/module_generator/plans/idea_synthesizer.plan.json` for the decomposed brick list.
- `@scripts/run_idea_synth_sample.py` to confirm expected CLI parameters and validations.
- `@_tmp/module_generator_run.log` (if present) for prior run timing and Claude transcripts.

## 7. Repository Status Snapshot (2025-09-23)
`git status --short` shows many additions:
- New/modified generator and CCSDK toolkit sources.
- Added sample summaries under `ai_working/idea_synthesizer/sample_summaries/`.
- Generated brick directories under `amplifier/idea_synthesizer/` plus helper scripts (`scripts/run_context_partitioner_sample.py`).
- Two staged context docs (including this one). Decide later which artefacts belong in source control vs regeneration output.
- Untracked `.claude/` state; safe to remove if needed.

## 8. Known Data / Config Defaults
| Variable | Default | Notes |
|----------|---------|-------|
| `AMPLIFIER_CLAUDE_PLAN_TIMEOUT` | 240 | Seconds to wait on plan call before cancelling. |
| `AMPLIFIER_CLAUDE_GENERATE_TIMEOUT` | 3600 (max 7200) | Seconds to allow for long generation runs. |
| `ORCH_MAX_PARTITION_TOKENS` | 8000 | Orchestrator converts to partition config; adjust if partitions overrun. |
| `ORCH_QUALITY_THRESHOLD` | 0.3 | Low to ensure sample fixtures produce ideas; plan to revisit. |
| `SAMPLE_FIXTURES_DIR` | `ai_working/idea_synthesizer/sample_summaries` | Sample runner default. |
| `SAMPLE_TIMEOUT_S` | 600 | Increased to tolerate slower runs. |

## 9. When Picking Back Up
1. Read `@ai_working/module_generator/BOOTSTRAP_INSTRUCTIONS.md` → it now points here, then to the strategic docs.
2. Skim the partial transcript if you need more colour.
3. Re-run the sample script manually to confirm the current failure mode still reproduces (`ContextPartitioner` import error).
4. Plan the generator changes (consider using `amplifier-cli-architect` to blueprint the fix before coding).
5. Implement generator updates, regenerate, and ensure the validation script runs successfully end-to-end.

## 10. Logging New Discoveries
When you uncover new quirks (e.g., additional missing exports, flaky retries), add an entry to `DISCOVERIES.md` using the Date/Issue/Root Cause/Solution/Prevention format. This keeps future sessions from repeating the same investigation.

Stay disciplined: regenerate, don’t hand-edit, and make the generator prove its output works.
