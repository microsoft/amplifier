# Errors & Fixes (Observed)

A quick reference of real issues seen during development and how to resolve them.

## amp: command not found
- Symptom: Shell prints `bash: amp: command not found`.
- Cause: Virtualenv not activated or install step not run.
- Fix:
  - `make install`
  - `source .venv/bin/activate`

## SDK/CLI not available
- Symptom: Generated tool raises a clear SDK/CLI error (by design, no fallbacks).
- Fix:
  - `npm i -g @anthropic-ai/claude-code`
  - Verify: `claude --help`
  - Re-run `make install` to ensure Python deps are synced.

## Generated tool has no run() in recipes.py
- Symptom: `amp tool create ...` fails with: `Generated tool has no run() in recipes.py and no valid plan for composition.`
- Cause: Plan didn’t include `steps`, and description could not be deterministically mapped to known kinds.
- Fix options:
  - Adjust your description to use the verbs and kinds the composer understands: discover_markdown, extract_structured, synthesize_catalog, draft_blueprints. Include a schema in square brackets when applicable (e.g., `[features, constraints, acceptance_criteria]`).
  - Or extend composer to add new kinds (see Next Work in the runbook).

## Unterminated string literal in generated recipes.py
- Symptom: `SyntaxError: unterminated string literal` in a generated tool’s `recipes.py`.
- Cause: Earlier emitters wrote raw multi-line literals.
- Status: Fixed in generator by building code line-by-line with explicit `\n` escapes and avoiding nested triple quotes.
- Fix if encountered: Remove the generated tool directory under `cli_tools/<name>/` and re-generate after pulling latest generator changes.

## Ideas pipeline produced empty or meta content
- Symptom: Summaries contain “I’m going to…” meta, or ideas array is empty.
- Cause: Earlier prompting didn’t gate content tightly.
- Status: The ideas template path includes content gating and allowed-source enforcement; dynamic composer support is planned to mirror these guards.
- Workaround: Use `--template ideas` for now when testing that flow.

## amp summarize CLI quirk
- Symptom: Root `amp summarize <files>` sometimes flagged extra args.
- Status: Known CLI parsing oddity in the root CLI; generated tools’ `summarize` commands work reliably.

