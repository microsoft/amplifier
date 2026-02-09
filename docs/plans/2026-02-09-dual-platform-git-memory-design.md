# Dual-Platform Development with Git-Based Memory - Design

**Date:** 2026-02-09
**Status:** Approved

## Goal

Set up dual-platform development where Claude Code is primary (development + deployment) and Gemini/OpenCode is support (review, analysis, alternative approaches). Both platforms share memory and coordination state via git notes.

## Background

The Gemini/OpenCode machine developed a significant extension to superpowers (psklarkins/superpowers fork) with:

1. **Git-Notes Coordination Bridge** - Cross-agent shared state via `refs/notes/superpowers`
2. **Git Memory System** - Persistent project knowledge (decisions, patterns, glossary)
3. **Model-Aware Skill Activation** - Auto-selects skills by persona/task

This work exists in the fork's main branch but isn't yet integrated into Claude Code's hook system.

## Architecture

### Shared Core (both platforms)

```
psklarkins/superpowers (git repo)
├── lib/                          # Shared Node.js core
│   ├── git-notes-state.js        # Read/write git notes
│   ├── state-schema.js           # Schema validation
│   ├── memory-ops.js             # Query/append memory
│   ├── record-finding.js         # Agent finding capture
│   ├── skills-core.js            # Skill discovery
│   └── index-skills.js           # Semantic indexer
├── commands/                     # CLI tools (both platforms)
│   ├── recall.js                 # Query memory
│   ├── memorize.js               # Store memory
│   ├── snapshot-memory.js        # Markdown export
│   ├── record-finding.js         # Record agent finding
│   ├── sync-context.js           # Git sync notes
│   └── push-context.js           # Push findings
├── skills/                       # Shared skills
├── .claude/                      # Claude Code wrapper
├── .opencode/                    # OpenCode wrapper
└── AMPLIFIER-AGENTS.md           # Agent mapping
```

### Cross-Machine Cooperation Flow

```
Gemini/OpenCode (Machine B)          GitHub            Claude Code (Machine A - Primary)
    │                                   │                        │
    ├─ record finding ────────────────► │                        │
    ├─ memorize decision ─────────────► │                        │
    ├─ git push notes ────────────────► │                        │
    │                                   │ ◄──── git fetch notes ─┤ (SessionStart hook)
    │                                   │                        ├─ recall context
    │                                   │                        ├─ develop + deploy
    │                                   │                        ├─ memorize findings
    │                                   │ ◄──── git push notes ──┤ (PreCompact hook)
    │ ◄──── git fetch notes ────────── │                        │
    ├─ recall findings                  │                        │
    └─ continue work                    │                        │
```

### Platform Roles

| Platform | Role | Responsibilities |
|----------|------|-----------------|
| Claude Code | Primary | Development, deployment, testing, git memory sync |
| Gemini/OpenCode | Support | Code review, long-context analysis, alternative approaches |
| Git Notes | Transport | Shared state between platforms |
| GitHub | Hub | Central storage for both code and notes |

### Integration Points

**Claude Code SessionStart hook:**
- `git fetch origin refs/notes/superpowers:refs/notes/superpowers`
- Read state, inject relevant memory into session context

**Claude Code PreCompact hook:**
- Push accumulated findings before context compaction

**Amplifier agents:**
- Read memory before starting work (recall)
- Store discoveries after completing work (memorize)

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Git sync hooks | integration-specialist | SessionStart/PreCompact git notes sync |
| Memory tool wiring | modular-builder | Adapt Node.js tools for Claude Code |
| Agent protocol | modular-builder | Add recall/memorize to agent definitions |
| Testing | test-coverage | Verify cross-platform sync |
| Cleanup | post-task-cleanup | Final hygiene pass |

## What We Don't Change

- Core superpowers skills (TDD, verification, red flags)
- Existing Claude Code plugin structure
- FuseCP-enterprise codebase (shared normally via git)
- Amplifier agent definitions (add memory protocol, don't rewrite)
