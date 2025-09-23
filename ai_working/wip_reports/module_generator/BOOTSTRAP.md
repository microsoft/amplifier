# Module Generator Context Bootstrap

Welcome back. This file is the single entry point when resuming work on the
module generator / CCSDK toolkit integration. Follow the checklist exactly.

## 1. Load the Right Context

Read (in order, no skipping):

1. `ai_working/wip_reports/module_generator/session_recap_2025-09-18.md` – captures
   exactly what changed in this session, current repo state, and pending actions.
2. `ai_working/wip_reports/module_generator/README.md` – overarching project scope,
   historical decisions, high-level TODOs prior to this session.
3. `ai_working/wip_reports/module_generator/ccsdk_patterns.md` – battle-tested CCSDK
   usage patterns referenced by the code.

Then review supporting artifacts:

- `ai_working/module_generator_example/` (contract/spec + example plan) to understand
  the inputs the generator consumes.
- `ai_working/module_generator_runs/idea_synthesizer/` (plan.md, generation_summary.md,
  `*.messages.jsonl`, todos, usage) for the exact dialogue Claude produced.
- `DISCOVERIES.md` (repo root) for environment pitfalls (cloud sync, retries).

## 2. Repository State Snapshot

- You are in a Git worktree (`amplifier-generator-cdx-from-chat`) linked to the parent
  repo `/home/brkrabac/repos/amplifier`. Any `git add/commit` targeting worktree files
  must be executed from the parent repo.
- Working branch: `generator-cdx-from-chat`.
- Modified files awaiting staging via parent repo:
  - `amplifier/ccsdk_toolkit/core/models.py`
  - `amplifier/ccsdk_toolkit/core/session.py`
  - `amplifier/module_generator/sdk.py`
- Proposed commit message (not yet committed):

  ```
  feat(toolkit): migrate module generator onto shared CCSDK session infrastructure
  ```

## 3. Immediate Next Tasks (from recap)

1. **Install missing dependency** – generated engine imports `slugify`. Run
   `uv add python-slugify` in `/home/brkrabac/repos/amplifier`.
2. **Validate generated module** – after installing slugify, execute:

   ```bash
   UV_CACHE_DIR=/tmp/uv_cache uv run python -m amplifier.idea_synthesizer.cli \
       tests/idea_synthesizer/fixtures/summaries --max-ideas 3 --limit 3 --verbose
   ```

3. **Stage, commit, push** – from parent repo, run the commands spelled out at the
   end of section 3 once validation looks good.

Do *not* modify generated idea synthesizer code until after recording the results; the
goal is to validate the module generator’s output.

## 4. Key Commands Reference

Planning / generation run (rerun only if contract/spec change):

```bash
LOG_LEVEL=DEBUG UV_CACHE_DIR=/tmp/uv_cache uv run python -m amplifier.module_generator \
    ai_working/module_generator_example/idea_synthesizer.contract.md \
    ai_working/module_generator_example/idea_synthesizer.impl_spec.md \
    --yes --plan-max-turns 120 --generate-max-turns 240
```

Toolkit + module generator tests:

```bash
UV_CACHE_DIR=/tmp/uv_cache uv run pytest tests/test_ccsdk_toolkit.py -q
UV_CACHE_DIR=/tmp/uv_cache uv run pytest tests/module_generator -q
UV_CACHE_DIR=/tmp/uv_cache make check
```

## 5. When Picking Up Work

- Activate env (`source .venv/bin/activate`) or rely on `uv run` wrappers.
- Ensure Claude CLI + SDK credentials available (see DISCOVERIES + toolkit README).
- Review `plan.todos.json` / `generation.todos.json` under
  `ai_working/module_generator_runs/idea_synthesizer/` for pending follow-ups the
  agent left during plan/build.
- Check `tests/idea_synthesizer/` results if rerunning; previous failures were due to
  generated code, not harness.

## 6. After Resuming

After finishing tasks, append a new dated recap (same directory) summarizing what you
did, so future sessions stay accurate.

_End of bootstrap instructions._
