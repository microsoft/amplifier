---
summary_path: permissions_and_hooks.summary.md
source_path: @.claude/settings.json
source_hash: fb7299a06383590d9ddfd089d27c719e189695b15dd9ee0c30b4f0827eda0a1f
summary_hash: 08093bd8817de498e741c91984506f539a23a5d7962e41cbf802c2f5850f379e
created_at: "2025-09-17T13:51:47Z"
title: Permissions & Hooks (settings.json, audit, guardrails)
tags: [permissions, hooks, audit, guardrails]
---

## Summary

Permissions are centralized in `.claude/settings.json` using explicit rules. Common write tools (Write/Edit/MultiEdit/Bash) should be disabled by default and enabled only in controlled phases. Hooks (SessionStart/PostToolUse/Stop) provide observability, cost logging, and policy enforcement. A secure baseline denies wide Bash access and requires explicit path scoping for Read/Write.


## Key Points

- Deny-by-default with explicit allowlists for tools and paths.
- Use hooks to log transcripts, costs, and diffs after writes.
- Switch from read-only to write-enabled phases intentionally.
- Prefer narrow Bash permissions; avoid wildcards.


## Risks & Constraints

- Over-broad permissions can cause destructive edits.
- Missing hooks reduce traceability and make debugging harder.