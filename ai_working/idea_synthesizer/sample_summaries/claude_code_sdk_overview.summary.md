---
summary_path: claude_code_sdk_overview.summary.md
source_path: @ai_context/claude_code/sdk/CLAUDE_CODE_SDK_OVERVIEW.md
source_hash: 5a5a5145d0862b5bfa711ce794f8bb333f93d72838045d01c51a8204fc3f1bda
summary_hash: f028ce518a3599c9d7bf0ef60c4fbba2aa1885da7e7c80352fafab8e38f2cd6b
created_at: "2025-09-17T13:51:47Z"
title: Claude Code SDK Overview (Sessions, Tools, Plan/Generate)
tags: [sdk, sessions, tools, permissions, streaming]
---

## Summary

The SDK exposes streaming sessions that honor the project's agents, memory files, permissions, and hooks. Developers control the working directory (cwd) and can include extra context dirs (add_dirs). Write operations require explicit permissions; read-only runs can be enforced by restricting tool lists. A practical workflow uses a dry 'plan' pass, then a write-enabled generation pass under acceptEdits. Telemetry includes session IDs, token/cost tracking, latency, and optionally TODO lifecycle.


## Key Points

- Sessions are resumable and can stream incremental responses.
- Subagents are auto-discovered from `.claude/agents/` (file-based).
- Permissions flow: deny/allow/ask; write tools must be explicitly enabled.
- Hooks can record transcripts, costs, and post-write checks.
- add_dirs brings ai_context and package code into scope cleanly.


## Risks & Constraints

- Misconfigured permissions lead to silent no-ops or unsafe writes.
- Large prompts require careful context budgeting to avoid truncation.