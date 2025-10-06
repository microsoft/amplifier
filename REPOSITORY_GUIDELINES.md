# Repository Guidelines

## Project Structure & Module Organization
Amplifier bundles automation, agent orchestration, and reference material in a single project. Python sources live in `amplifier/`, long-form AI context in `ai_context/`, and working notes plus decision history in `ai_working/`. Tests reside in `tests/` alongside targeted fixtures. Helper scripts stay in `scripts/`, data artifacts in `data/`, and documentation in `docs/`. Leave `tools/` untouched; it is reserved for maintainer-managed build plumbing. Update `ai_working/decisions/` and `DISCOVERIES.md` whenever you introduce new patterns or lessons.

## Build, Test, and Development Commands
- `make install` — Sync Python deps with `uv` and ensure CLI tooling is present.
- `make check` — Run formatting, linting, and type-checking in one pass.
- `make test` / `make smoke-test` — Execute the full pytest suite or the fast sanity subset.
- `make knowledge-update` — End-to-end content ingestion and synthesis; run after new knowledge inputs.
- `make ai-context-files` — Regenerate AI-facing documentation when specs change.
Use `uv run <command>` for ad-hoc Python entry points.

## Coding Style & Naming Conventions
Target Python 3.11+, 4-space indentation, double-quoted strings, and 120-character lines (enforced by Ruff). Keep imports ordered via Ruff’s isort rules and include type hints, even for `self`. Manage dependencies with `uv add` rather than hand-editing `pyproject.toml`. Prefer descriptive module and function names; pluralize directories containing collections (e.g., `tasks/`) and keep click commands lowercase with hyphenated names.

## Testing Guidelines
Pytest with `pytest-asyncio` powers the suite. Place tests under `tests/` using `test_<feature>.py` and `Test<Class>` naming. Cover new behavior and edge cases; use `pytest.mark.asyncio` for coroutine tests. For coverage spot checks, run `uv run pytest --cov`. Always execute `make check` and at least `make smoke-test` before submitting changes.

## Commit & Pull Request Guidelines
Follow Conventional Commits (`feat:`, `fix:`, `chore:`, etc.) and keep each change focused on a vertical slice. Reference related issues in the body, summarize agent usage or new decisions, and note any documentation updates. Pull requests should include validation details (commands run, screenshots when UI-affecting) and call out follow-up work explicitly.

## Agent Workflow Expectations
Prioritize the specialized agents catalogued in `.claude/AGENTS_CATALOG.md`; spin up the right expert before tackling architecture, debugging, or synthesis tasks. Record noteworthy findings in `DISCOVERIES.md` and capture strategic choices in `ai_working/decisions/` so future agents inherit the rationale. Apply the incremental processing pattern when building long-running automations so progress survives interruptions.
