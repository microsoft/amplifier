# Memento: How Future‑Me Restores Context Fast

Read this file first when resuming with no prior chat history. It bootstraps context and provides copy‑paste commands.

## TL;DR (10–15 minutes)
- Environment
  - `make install && source .venv/bin/activate`
  - Confirm CCSDK CLI: `claude --help` (if missing: `npm i -g @anthropic-ai/claude-code`)
  - Validate project: `make check`
- Read in order
  1) `ai_context/IMPLEMENTATION_PHILOSOPHY.md` (how we build)
  2) `ai_context/MODULAR_DESIGN_PHILOSOPHY.md` (how we structure)
  3) `DISCOVERIES.md` (latest entries first)
  4) `ai_working/ENGINEERING_JOURNAL_2025-09-23.md` (session summary)
  5) `ai_working/ccsdk-amplifier-improvement-plan.md` (toolkit roadmap)
- Open key code
  - `amplifier/microtasks/recipes/tool.py` (generator/composer)
  - `amplifier/microtasks/recipes/tool_philosophy.py` (planning + advisor preamble)
  - `amplifier/ccsdk_toolkit/` (core sessions, logging, defensive I/O)
- Run a smoke test (see below)

## What We’re Building (Scope)
- An Amplifier CLI that generates standalone CLI tools which:
  - Use Claude Code SDK via our `ccsdk_toolkit` (no fallbacks; fail fast with clear errors)
  - Stream progress (print job_id + artifacts dir; per‑step ticks)
  - Save artifacts incrementally for resume (status.json, results.json, per‑item files)
  - Apply metacognitive loops where useful (plan → synthesize → critique/repair)

## Current State (2025‑09‑23)
- Generator emits self‑contained tools with:
  - `microtasks/llm.py` using `amplifier.ccsdk_toolkit.core` (ClaudeSession/SessionOptions)
  - `microtasks/orchestrator.py` using toolkit logger + defensive JSON writes
  - CLI prints job_id/artifacts and step ticks
- Composer (no template) understands these step kinds:
  - `discover_markdown`, `extract_structured`, `synthesize_catalog`, `draft_blueprints`
  - If plan lacks `steps`, generator derives them from the description and writes `plan.json` (explicit, visible)
- “Ideas” pipelines exist as a template (summarize_each → synthesize_ideas → expand_ideas). Extending dynamic composer to support these is the next task.

## Key Concepts and Files
- Generator/composer
  - `amplifier/microtasks/recipes/tool.py` — writes `cli_tools/<name>/...`; composes recipes from `plan.json`
  - `amplifier/microtasks/recipes/tool_philosophy.py` — creates plan/code prompts; includes the “amplifier‑cli‑architect” preamble to bias outputs
- CCSDK toolkit
  - `amplifier/ccsdk_toolkit/core/` — `ClaudeSession`, `SessionOptions`, `SDKNotAvailableError`
  - `amplifier/ccsdk_toolkit/logger/` — progress logging with `stage_start/complete`
  - `amplifier/ccsdk_toolkit/defensive/` — JSON extraction, retrying file I/O
- References
  - `DISCOVERIES.md` — non‑obvious pitfalls and fixes (string emission, no‑defaults policy)
  - `ai_working/ccsdk-amplifier-improvement-plan.md` — WIP toolkit/reporting guidance

## Glossary (project‑specific)
- Composer: Code that turns a structured plan (`plan.json` with `steps`) into a runnable `recipes.py`.
- Step kinds (current): discover_markdown, extract_structured, synthesize_catalog, draft_blueprints.
- Artifacts dir: `.data/<tool>/runs/<job_id>/artifacts/` — location for `status.json`, outputs, and `results.json`.
- No fallbacks: Do not continue with hidden defaults when inputs are insufficient; fail fast with clear error.

## Quick Smoke Tests
1) Environment
```
make install
source .venv/bin/activate
claude --help
make check
```

2) Dynamic compose (no template)
```
amp tool create spec-weaver2 --desc "Goal: Given Markdown product specs, 1) discover first N files; 2) extract structured requirements per file with keys [features, constraints, acceptance_criteria] (resume-friendly); 3) synthesize a deduplicated cross-doc catalog with source mapping; 4) draft implementation blueprints with sections [Context, Interfaces, Risks, Test Strategy, Milestones]; 5) stream progress and write artifacts/status incrementally." && \
amp tool install spec-weaver2 && \
spec-weaver2 run --src docs --limit 3
```

3) “Ideas” (temporary template path until composer supports these kinds)
```
amp tool create ideas-demo --desc "Process .md files: summarize_each → synthesize_ideas → expand_ideas with resume and progress." --template ideas && \
amp tool install ideas-demo && \
ideas-demo run --src docs --limit 3
```

## Troubleshooting (observed in this repo)
- `amp: command not found` — run `make install` then `source .venv/bin/activate`.
- SDK/CLI missing — ensure `claude --help` works; install globally via npm if needed.
- “Generated tool has no run()…” — your description didn’t map to known step kinds and derivation failed. Add explicit verbs (discover/extract/synthesize/blueprint) or extend composer (see Next Work).
- Unterminated string literal in generated tool — addressed by line‑by‑line emitters; if encountered, delete the generated `cli_tools/<name>` and re‑generate after fixing emitter.
- “Ideas” produced empty outputs — earlier versions sometimes returned meta text; current guards rewrite summaries and enforce allowed sources; still planned for composer path.
- Root `amp summarize` CLI quirk — known; generated tools’ summarize commands work reliably.

## Active Work Items (resume here)
1) Add composer support for ideas pipelines:
   - Step kinds: `summarize_each`, `synthesize_ideas`, `expand_ideas` with content gates and repair passes.
   - Enforce allowed‑source grounding and required sections/length in expansions.
   - Optional: worker pool (3–4) for summarize_each; preserve resume.
2) CLI UX:
   - `amp tail <job_id>` to stream `status.json` updates for long runs.
3) Generator golden tests:
   - Assert generated `recipes.py` parses (AST) and exports `run`.
   - Verify escaped regex/newlines and that `make check` remains green after generation.

## Decision Highlights
- No fallbacks — if SDK/CLI missing or plan lacks steps, fail fast. Any derived plan must be explicit and saved as `plan.json`.
- Centralize SDK/logging/I/O in CCSDK toolkit to reduce brittle emitters.
- Use “amplifier‑cli‑architect” advisor in planning to align with Amplifier philosophies and prior learnings.

## Read Next
- @ai_working/ENGINEERING_JOURNAL_2025-09-23.md
- @DISCOVERIES.md (latest entries)
- @ai_working/ccsdk-amplifier-improvement-plan.md

