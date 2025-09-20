# Decision: Microtask-Driven CLI with Claude Code SDK (MVP)

Date: 2025-09-15

## Context

We need a working, microtask-driven CLI that mirrors Amplifier’s “recipes” (plan → execute → verify), integrates with the Claude Code SDK, and adheres to our Implementation and Modular Design philosophies. The result should be testable offline and upgrade seamlessly when the Claude CLI/SDK is available.

## Decision

Implement a minimal microtask engine under `amplifier/microtasks/` with:

- A file-based `JobStore` that writes `results.json` after each step (incremental processing).
- `MicrotaskOrchestrator` running deterministic steps with graceful partial-failure handling.
- `LLM` wrapper that uses `claude-code-sdk` when the Claude CLI is runnable, else a deterministic local fallback.
- A working code “recipe” (plan → implement → test → refine).
- A Click-based CLI registered as `amp`.

## Rationale

- Ruthless simplicity: single vertical slice that works now; clean public contracts.
- Modular “bricks and studs”: `models`, `store`, `llm`, `orchestrator`, `recipes` are self-contained.
- Zero-BS principle: fully functional MVP; fallback mode still generates runnable code and tests.
- Configuration SSoT: reuses existing project config; keeps CLI lightweight.

## Alternatives Considered

1. Full async pipeline end-to-end – higher complexity for little immediate value; avoided.
2. Database-backed store – unnecessary for MVP; file-based writes are sufficient and faster to implement.
3. Hard dependency on Claude – rejected to preserve offline testability and reliability in CI.

## Impacts

- Adds `amp` CLI entrypoint and new `amplifier.microtasks` module.
- New tests cover the end-to-end flow with fallback.
- SDK path validated via `claude --help`; if unavailable, fallback kicks in reliably.

## Review Triggers

- Need for parallel execution of independent steps.
- Recipes beyond coding (analysis, knowledge synthesis) are requested.
- Persistent run metadata across machines or multi-user environments.

## Prevention / Next Steps

- Keep recipes small and self-contained. Add new recipes in `amplifier/microtasks/recipes/`.
- Consider environment variable to force fallback (`AMPLIFIER_FORCE_LOCAL_LLM`).
- Add richer validation (anti-sycophancy checks) post-LLM step as separate validators.

