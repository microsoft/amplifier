# Memento: How Future-Me Restores Context Fast

Read this file first when resuming work with no prior chat history. It bootstraps the full context and tells you exactly what to run and read.

## TL;DR (10 minutes)
- Ensure env works: `make install && source .venv/bin/activate && claude --help`
- Skim these in order:
  1) `ai_context/IMPLEMENTATION_PHILOSOPHY.md`
  2) `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`
  3) `DISCOVERIES.md` (latest entries at bottom)
  4) `ai_working/ENGINEERING_JOURNAL_2025-09-23.md` (today’s session summary)
  5) `ai_working/ccsdk-amplifier-improvement-plan.md` (toolkit roadmap)
- Open the code you’ll be touching:
  - `amplifier/microtasks/recipes/tool.py` (generator)
  - `amplifier/microtasks/recipes/tool_philosophy.py` (planner/generator prompts)
  - `amplifier/microtasks/llm.py` (SDK wrapper for microtasks core)
  - `amplifier/ccsdk_toolkit/` (sessions, logging, defensive I/O)
- Validate the repo: `make check`
- Try a compose tool: see “Quick Smoke Tests”.

## What We’re Building
- A microtask‑driven “Amplifier CLI” that can itself generate robust, standalone CLI tools using Claude Code SDK.
- Generated tools must:
  - Use CCSDK (no fallbacks). Fail fast with clear errors if SDK/CLI missing.
  - Stream progress (job_id on start; per-step ticks).
  - Save artifacts incrementally (resume-friendly).
  - Apply metacognitive planning/evaluation loops (planning → synthesis → critique/repair) when appropriate.

## Current State (as of 2025-09-23)
- Generator emits self-contained tools with:
  - `microtasks/llm.py` using `amplifier.ccsdk_toolkit.core` (ClaudeSession/SessionOptions).
  - `microtasks/orchestrator.py` using toolkit logger + defensive file I/O.
  - CLI with progress printing and artifacts journaling.
- Composer path (no template) supports step kinds:
  - `discover_markdown`, `extract_structured`, `synthesize_catalog`, `draft_blueprints`.
  - If the plan lacks steps, generator derives steps from the description heuristically (still no implicit defaults; it writes a concrete plan.json and composes from it).
- Ideas-style pipelines (summarize_each → synthesize_ideas → expand_ideas) existed earlier and work via a template branch; adding them to dynamic compose is next.

## Key Files To Understand
- Generator & planning
  - `amplifier/microtasks/recipes/tool.py` — main generator; composition and emitted scaffolds.
  - `amplifier/microtasks/recipes/tool_philosophy.py` — plan/code prompts; injects “amplifier-cli-architect” guidance.
  - `DISCOVERIES.md` — pitfalls + fixes (string emission, no-defaults policy, CCSDK integration).
- Toolkit
  - `amplifier/ccsdk_toolkit/core/` — ClaudeSession, options, availability errors.
  - `amplifier/ccsdk_toolkit/logger/` — structured logging with stage markers.
  - `amplifier/ccsdk_toolkit/defensive/` — JSON parsing helper, retrying file I/O.

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

3) Ideas-style (temporary, template path until compose grows these kinds)
```
amp tool create ideas-demo --desc "Process .md files: summarize_each → synthesize_ideas → expand_ideas with resume and progress." --template ideas && \
amp tool install ideas-demo && \
ideas-demo run --src docs --limit 3
```

## Active Work Items (resume here)
1) Add dynamic compose kinds for ideas pipelines:
   - `summarize_each`, `synthesize_ideas`, `expand_ideas` with strict content gates and repair passes.
   - Enforce allowed-source grounding and section/length minima.
   - Parallelize summarize_each (worker pool 3–4), preserving resume semantics.
2) CLI UX: optional `amp tail <job_id>` to follow long runs (reads artifacts/status.json).
3) Golden tests for generator:
   - Generated `recipes.py` parses (AST) and exports `run`.
   - No unterminated strings; regexes escaped.
   - `make check` remains green after generation.

## Decision Highlights
- No fallbacks policy: if SDK/CLI missing or plan has no steps → fail fast; do not emit hidden defaults.
- Emitted scaffolds rely on CCSDK toolkit for sessions/logging/I/O — reduces duplication and hard-to-test string emitters.
- Planning prompt includes “amplifier-cli-architect” to bias toward Amplifier patterns.

## If Something Breaks
- “has no run() in recipes.py”: description didn’t map to known step kinds and derivation failed. Add explicit step verbs (discover/extract/synthesize/blueprint) or extend compose kinds.
- Unterminated strings in generated code: see `DISCOVERIES.md` entry 2025-09-20; ensure emitters build code line-by-line and escape newlines in literals.
- SDK errors: verify `claude --help` works; re-run `make install`.

## Read Next
- @ai_working/ENGINEERING_JOURNAL_2025-09-23.md
- @DISCOVERIES.md (bottom-up)
- @ai_working/ccsdk-amplifier-improvement-plan.md (toolkit roadmap)

