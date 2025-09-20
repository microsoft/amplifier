Microtask Engine (Brick)

Purpose
- Run small, dependable “recipes” (plan → implement → test → refine)
- Persist progress after every step
- Require Claude Code SDK/CLI; no fallbacks

Contract
- Python API: `from amplifier.microtasks import run_code_recipe`
- CLI: `amp code "<goal>"`

Files
- `models.py` – data contracts and job state
- `store.py` – file-based persistence to `.data/microtasks/<job_id>/results.json`
- `llm.py` – Claude SDK wrapper with deterministic fallback
- `orchestrator.py` – step runner with partial-failure handling
- `recipes/code.py` – MVP recipe
- `cli.py` – Click CLI entry

Usage
```bash
amp code "add two numbers"
amp list
amp show <job_id>
```

Notes
- No fallbacks: if the SDK/CLI isn’t available, commands fail early with clear guidance.
- This module follows the bricks-and-studs philosophy; new recipes live in `recipes/` with the same contract.
