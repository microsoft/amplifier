# Rehydrate Runbook (Step‑by‑Step)

Follow this checklist to fully restore context and validate the system without the chat transcript.

## 1) Environment Setup
- `make install`
- `source .venv/bin/activate`
- Verify CCSDK CLI: `claude --help` (install with `npm i -g @anthropic-ai/claude-code` if missing)
- Optional: ensure PNPM global bin on PATH if needed (`pnpm bin -g`)

## 2) Core Reading (links)
- `ai_context/IMPLEMENTATION_PHILOSOPHY.md`
- `ai_context/MODULAR_DESIGN_PHILOSOPHY.md`
- `DISCOVERIES.md` (focus on 2025‑09‑20 and 2025‑09‑23 entries)
- `ai_working/ENGINEERING_JOURNAL_2025-09-23.md`
- `ai_working/ccsdk-amplifier-improvement-plan.md`

## 3) Files to Inspect (in editor)
- Generator: `amplifier/microtasks/recipes/tool.py`
- Planner: `amplifier/microtasks/recipes/tool_philosophy.py`
- Toolkit: `amplifier/ccsdk_toolkit/` (core/logger/defensive)

## 4) Sanity Checks
- `make check` should pass (format, lint, type, stub scan)
- Quick import check of generated tool structure after a run (AST parse)

## 5) Dynamic Compose Smoke Test
```
amp tool create spec-weaver2 --desc "Goal: Given Markdown product specs, 1) discover first N files; 2) extract structured requirements per file with keys [features, constraints, acceptance_criteria] (resume-friendly); 3) synthesize a deduplicated cross-doc catalog with source mapping; 4) draft implementation blueprints with sections [Context, Interfaces, Risks, Test Strategy, Milestones]; 5) stream progress and write artifacts/status incrementally." && \
amp tool install spec-weaver2 && \
spec-weaver2 run --src docs --limit 3
```
- Expect: job_id + artifacts path printed immediately; per‑step ticks; artifacts under `.data/spec-weaver2/runs/<job_id>/artifacts`.

## 6) “Ideas” Path (Template for now)
```
amp tool create ideas-demo --desc "Process .md files: summarize_each → synthesize_ideas → expand_ideas with resume and progress." --template ideas && \
amp tool install ideas-demo && \
ideas-demo run --src docs --limit 3
```
- Expect: summaries in `summaries/`, ideas in `ideas/`, incremental `status.json`.

## 7) Troubleshooting
- `amp: command not found` → activate venv; ensure `amp` installed via `make install`.
- CCSDK errors → ensure `claude` CLI available; re-run `make install`.
- “no run() in recipes.py” → description didn’t map to recognized steps, and derivation failed. Use the verbs (discover/extract/synthesize/blueprint) or extend composer.
- Unterminated strings → regenerate after fixing emitter; avoid raw multi‑line literals in emitters.

## 8) Where To Resume Coding
- Add composer support for ideas step kinds in `tool.py` (search for `_compose_recipes_from_plan2` usage and step resolver) and update `_cli_py` wiring if needed.
- Keep to no‑fallback policy: plans must have explicit steps; if derived, write them to `plan.json`.

## 9) Hand‑off Summary
- The generator now emits CCSDK‑backed scaffolds and strict progress journaling.
- The composer path is reliable for the 4 supported step kinds and fails fast otherwise.
- Next milestone: dynamic “ideas” pipelines with the same rigor as the 4‑stage compose flow.

