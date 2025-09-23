# Engineering Journal — 2025-09-23

Purpose: Capture enough detail that a fresh agent can fully rehydrate context and resume work without the chat transcript.

## Goals
- Build an “Amplifier CLI” that can generate robust, standalone tools powered by Claude Code SDK.
- Enforce: no fallbacks, progress streaming, resume-safe artifacts, and metacognitive loops.

## What Landed Today
1) Generator now emits CCSDK-backed scaffolds (no fallbacks)
   - `microtasks/llm.py` uses `amplifier.ccsdk_toolkit.core` (ClaudeSession/SessionOptions).
   - `microtasks/orchestrator.py` uses toolkit logger + retrying JSON writes.
2) Composer policy tightened
   - Removed implicit default steps; generator fails fast if plan has no steps.
   - If plan.txt lacks steps, derive a concrete `steps` array from the description heuristically and compose from that.
3) Planning prompt upgrade
   - Injected “amplifier-cli-architect” preamble to bias toward Amplifier patterns and CCSDK toolkit usage.
4) Docs
   - Added DISCOVERIES entry covering string-literal pitfalls, CCSDK integration, and no-defaults policy.

## Known Gaps / Next Work
1) Dynamic compose for ideas-kind pipelines
   - Add support for `summarize_each`, `synthesize_ideas`, `expand_ideas` in composer (not only the template). Include:
     - Content gating (remove “I’m going to…” meta), length thresholds.
     - Allowed-source enforcement in synthesis outputs.
     - Expansion section enforcement (## Context, ## Benefits, ## Risks, ## Plan) with repair pass.
     - Optional small worker pool for summarize_each.
2) Progress tailing
   - Small `amp tail <job_id>` to follow artifacts/status.json in real time.
3) Golden tests for generator outputs
   - Parse check (ast), export `run()`, escaped regex and literals.

## Why These Decisions
- CCSDK toolkit centralization reduced fragile string emission and repetitive boilerplate; it also provides robust logging and I/O.
- No-defaults composer prevents silent misbehavior and aligns with user’s “no fallbacks” mandate.
- Architect preamble ensures generated plans/tools follow Amplifier’s philosophies consistently.

## How To Validate (Smoke)
1) Environment
```
make install && source .venv/bin/activate && claude --help && make check
```
2) Dynamic compose example
```
amp tool create spec-weaver2 --desc "Goal: Given Markdown product specs, 1) discover first N files; 2) extract structured requirements per file with keys [features, constraints, acceptance_criteria] (resume-friendly); 3) synthesize a deduplicated cross-doc catalog with source mapping; 4) draft implementation blueprints with sections [Context, Interfaces, Risks, Test Strategy, Milestones]; 5) stream progress and write artifacts/status incrementally." && \
amp tool install spec-weaver2 && \
spec-weaver2 run --src docs --limit 3
```

## Notable Artifacts & Paths
- Generated tools write to `.data/<tool>/runs/<job_id>/artifacts/`:
  - `discover.json`, `findings.json`, `findings/*.json`, `catalog.json`, `blueprints/*.md`, `status.json`, `results.json`.

## Open Questions
- Where to configure per-step CCSDK options per tool vs per-call? (Toolkit supports; hooks into generator TBD.)
- How much parallelism by default without exceeding provider rate limits? (Start with 3–4 workers.
)

## References
- @ai_context/IMPLEMENTATION_PHILOSOPHY.md
- @ai_context/MODULAR_DESIGN_PHILOSOPHY.md
- @ai_working/ccsdk-amplifier-improvement-plan.md
- @DISCOVERIES.md
- Code: `amplifier/microtasks/recipes/tool.py`, `amplifier/microtasks/recipes/tool_philosophy.py`, `amplifier/ccsdk_toolkit/`

