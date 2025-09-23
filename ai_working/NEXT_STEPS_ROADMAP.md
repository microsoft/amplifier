# Next Steps Roadmap (Actionable)

This list turns the current plan into concrete, reviewable tasks with acceptance criteria.

## 1) Add dynamic composer support for ideas pipelines
- Goal: Support step kinds `summarize_each`, `synthesize_ideas`, `expand_ideas` in the no-template path.
- Tasks:
  - Implement step resolvers in `amplifier/microtasks/recipes/tool.py` compose path, mirroring the behavior in the ideas template.
  - Enforce guards: summary bullet rewrite, allowed-source enforcement, expansion sections (## Context, ## Benefits, ## Risks, ## Plan) and length thresholds, one repair pass.
  - Optional parallelism: worker pool (3–4) for `summarize_each`, resume-friendly.
- Acceptance:
  - `amp tool create ideas-auto --desc "…ideas flow…"` without `--template` creates a tool that runs end-to-end on `docs/` and produces non-empty `ideas/*.md` with required sections.

## 2) Tail long runs
- Goal: Follow progress in real-time for long microtasks.
- Tasks:
  - Add `amp tail <job_id>` command (reads artifacts/status.json on interval, prints stage + item counters).
- Acceptance:
  - While a run is executing, `amp tail <job_id>` shows live stage updates until completion.

## 3) Generator golden tests
- Goal: Prevent regressions in emitted code structure.
- Tasks:
  - Add tests that generate a tool, AST-parse `recipes.py`, assert `def run(` exists, and that `make check` stays green.
  - Verify regex/newline escaping for emitted code (no unterminated strings).
- Acceptance:
  - CI job passes on all supported Python versions in the repo (3.11+).

## 4) Clarify root CLI summarize command
- Goal: Remove ambiguity observed earlier with `amp summarize` argument parsing.
- Tasks:
  - Revisit Click decorators order/signature in `amplifier/microtasks/cli.py` summarize command; add test case.
- Acceptance:
  - `amp summarize --purpose "…" path/to/file.md` works consistently.

