# Module Generator Architecture (Microtask Edition)

This document captures the target decomposition for the module generator so each behaviour is testable on its own yet composable into larger workflows.

## Microtools

| Module | Responsibility | Inputs | Outputs |
| --- | --- | --- | --- |
| `context.py` | Build `GenContext` from CLI inputs and repo inspection | CLI args | `GenContext` dataclass |
| `planner/template.py` | Produce the canonical plan prompt template | `GenContext`, contract text, spec text | prompt string |
| `planner/service.py` | Call Claude to obtain a structured plan using the template | prompt string | plan dict + telemetry |
| `planner/store.py` | Persist/load plan artefacts (`.json`) | plan dict | filesystem artefact |
| `decomposer/specs.py` | For each plan brick, synthesise or locate contract/spec files | plan brick | `(contract_path, spec_path)` |
| `executor/recipe.py` | Walk the plan and dispatch brick-level work | plan dict | execution log |
| `executor/run_submodule.py` | Invoke the generator recursively for a brick | `GenContext`, brick data | success status |
| `executor/verify.py` | Ensure generated files exist & match plan entries | plan brick | validation result |
| `sdk/claude.py` | All Claude SDK interactions (plan + generate, with retries) | prompt payloads | text + metadata |
| `sdk/retry.py` | Retry/backoff + transcript augmentation on parse errors | raw response, error | new prompt instructions |

All public microtools expose simple functions so we can test and script them individually.

## Orchestration Flow

1. CLI builds `GenContext` and decides whether to reuse an existing plan.
2. Planner template + service generate a plan dict; `store.py` saves it under `ai_working/module_generator/plans/<module>.json` alongside metadata.
3. `executor/recipe.py` iterates over `plan["bricks"]`:
   - `specs.py` resolves/generates contract/spec documents for the brick.
   - `run_submodule.py` calls the generator recursively with `--use-plan` for the brick (supports nesting).
   - `verify.py` confirms the expected files exist.
4. After all bricks succeed, the top-level executor may run an optional integration verification step (e.g. `make check`).

## Plan Format

Plans are stored as JSON with this structure:

```json
{
  "module": "idea_synthesizer",
  "created_at": "2025-09-17T12:10:00Z",
  "claude_session": "abc-123",
  "bricks": [
    {
      "name": "loader",
      "description": "Load summaries and compute manifest hash",
      "contract_path": "ai_working/idea_synthesizer/loader.contract.md",
      "spec_path": "ai_working/idea_synthesizer/loader.impl_spec.md",
      "target_dir": "amplifier/idea_synthesizer/loader",
      "type": "python_module"
    }
  ]
}
```

The executor trusts this plan and refuses to proceed if required fields are missing.

## Persistence Strategy

- Plans live in `ai_working/module_generator/plans/<module>.json`.
- Brick-level contract/spec documents reside under `ai_working/<module>/<brick>.*.md`.
- Generated code stays under `amplifier/<module>/<brick>/` per plan.

This makes the entire process restartable and auditable.

## Testing Strategy

Each microtool gets a dedicated unit test file (e.g. `tests/test_plan_store.py`). Composition tests exercise the end-to-end recipe using fixtures. The CLI test simply ensures flags wire up the orchestrator correctly.
