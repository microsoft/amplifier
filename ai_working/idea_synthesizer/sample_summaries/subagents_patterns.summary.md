---
summary_path: subagents_patterns.summary.md
source_path: @.claude/agents/AGENTS.md
source_hash: 49c4c2dc775789d30c1c914f87c4a0b88a0c1d17f519153c8d2c87184519e4e5
summary_hash: 6f7bb86d7a6498c7021ada148674b3ae2ebb59a1a1e92347e7f8a1ceff1b2683
created_at: "2025-09-17T13:51:47Z"
title: Subagents & Patterns (Builder, Tester, Verifier)
tags: [agents, subagents, parallelism, context-isolation]
---

## Summary

Subagents encapsulate specialized roles—e.g., 'modular-builder' for implementation, 'test-coverage' for tests, and 'attribution-verifier' for provenance checks. They are defined as Markdown files and auto-loaded by the SDK. Parallel use of subagents reduces context bleed and speeds multi-step workflows. Prompts emphasize crisp inputs/outputs, predictable file operations, and deconflicted responsibilities.


## Key Points

- Agents live in `.claude/agents/*.md`; no runtime creation API.
- Use separate agents for design-check, synthesis, testing, and security.
- Keep each agent’s tool permissions minimal for safety.
- Parallel fan-out is valuable for independent tasks.


## Risks & Constraints

- Too many agents can fragment context and increase overhead.
- Ambiguous scopes cause subagents to step on each other’s outputs.