# Repository Guidelines

## Project Structure & Module Organization
- Core services live in `amplifier/` (CLI entrypoints in `cli.py`, domain modules under subpackages like `knowledge_mining/` and `knowledge_synthesis/`).
- Shared specs, decisions, and agent artifacts are in `ai_working/` and `.claude/`; consult `ai_working/decisions/` before altering architecture.
- Automated and manual tests reside in `tests/` and `amplifier/smoke_tests/`; docs, playbooks, and summaries live in `docs/` and the root Markdown guides.

## Build, Test, and Development Commands
- `make install` creates the uv-managed virtualenv and installs dependencies.
- `make check` runs formatting (ruff), linting, and pyright type checks; run it before pushing.
- `make test` or `uv run pytest` executes the pytest suite; target a module with `uv run pytest tests/test_parallel_execution.py -v` when iterating.
- `start-claude.sh` launches the Amplifier CLI stack; stop it with Ctrl+C once manual testing is complete.

## Coding Style & Naming Conventions
- Python 3.11+, 4-space indentation, and exhaustive type hints (`Self` for methods, `Optional[...]` for nullable values) are mandatory.
- Ruff enforces formatting and lint rules (120-char lines); let it manage imports and docstring spacing.
- Prefer descriptive module and function names (e.g., `resilient_miner.py`, not `misc_utils.py`) and keep configuration in `pyproject.toml` as the single source of truth.

## Testing Guidelines
- Pytest drives both unit and integration coverage; mirror the module path (`tests/test_stub_detection.py`) and use `Test...` classes with `test_...` methods.
- Save intermediate artifacts during long-running knowledge mining tests to honor the incremental processing and partial failure patterns documented in `DISCOVERIES.md`.
- Smoke flows under `amplifier/smoke_tests/` should still run via pytest; add fixtures in `tests/conftest.py` when sharing setup.

## Commit & Pull Request Guidelines
- Follow Conventional Commits (`feat:`, `fix:`, `docs:`) as seen in recent history; keep subjects imperative and under 72 characters.
- Each PR should describe scope, link to issues or decision records, and note test evidence (`make check`, `make test`, manual CLI run).
- Call out agent choices and updates to `DISCOVERIES.md` or `.claude` artifacts in the PR body so reviewers can track workflow impacts.

## Agent Workflow Expectations
- Before significant work, review `.claude/AGENTS_CATALOG.md` and spin up specialized agents (e.g., `modular-builder`, `test-coverage`) that match the task.
- Document non-obvious findings in `DISCOVERIES.md` using the standard template to keep future agents productive.
