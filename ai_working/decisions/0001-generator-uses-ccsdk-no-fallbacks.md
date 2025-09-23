# 0001 – Generator uses CCSDK toolkit; no implicit fallbacks

- Date: 2025-09-23
- Status: Accepted

## Context
Generated tools previously embedded ad-hoc SDK usage and sometimes wrote fragile string literals, leading to parsing issues and inconsistent progress handling. Composer also attempted hidden defaults when plans were empty, violating our “no fallbacks” policy.

## Decision
1) Emitted tools must use `amplifier.ccsdk_toolkit` for Claude sessions, logging, and defensive I/O.
2) Composer must not inject implicit default steps. If a plan lacks steps, fail fast or write an explicit derived `plan.json` visible to users.
3) Planning prompts include an “amplifier-cli-architect” preamble to bias toward Amplifier patterns.

## Consequences
Pros:
- Centralized, robust SDK integration and progress logging.
- Fewer parsing failures in emitted code.
- Transparent planning/composition; easier debugging and resume.

Cons:
- Slightly more up-front structure in emitted scaffolds.
- Fails fast when step kinds aren’t recognized (requires clearer descriptions or extending composer).

## Alternatives Considered
- Continue with raw LLM code emission → rejected (too brittle).
- Keep default steps when plan is empty → rejected (violates policy; confusing behavior).

## Review Triggers
- Adding new step kinds (e.g., ideas pipeline) to the composer.
- Changes in Claude Code SDK interfaces.

