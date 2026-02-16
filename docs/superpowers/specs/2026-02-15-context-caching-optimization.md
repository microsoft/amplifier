# Context Caching Optimization (Gold Prefix) Design Spec

**Date:** 2026-02-15
**Status:** Implemented
**Branch:** feature/platform-aware-hooks

## Problem

Gemini 3's context caching on OpenCode requires bit-for-bit prefix stability to maximize "Cache Read" operations and minimize TPM limit hits. The Amplifier hooks inject dynamic content (date, git status, environment) that invalidates the cache every session. Additionally, hardcoded paths prevented the same codebase from running on both the Claude Code machine and the Gemini/OpenCode machine.

## Goal

1. Restructure hook output into Frozen Zone (stable) and Churn Zone (dynamic) to maximize Gemini context caching
2. Add platform detection so both Claude Code and OpenCode machines run from the same codebase
3. Keep Gemini-specific optimizations gated so they don't add noise to Claude Code sessions
4. Maintain `.claude/agents/` as canonical source with automated sync to OpenCode format

## Architecture

### Platform Detection

Module: `.claude/tools/platform_detect.py`

Detects which machine by checking root folder existence:
- `C:/claude/amplifier` exists → Claude Code (IS_CLAUDE_CODE=True)
- `C:/Przemek` exists → OpenCode/Gemini (IS_OPENCODE=True)

Exports: `IS_CLAUDE_CODE`, `IS_OPENCODE`, `AMPLIFIER_ROOT`, `SUPERPOWERS_FALLBACK`

### Gold Prefix Strategy (OpenCode only)

The prompt is divided into two zones:

**Frozen Zone (stable prefix):**
- Core identity and mandates
- Agent manifest (AMPLIFIER-AGENTS.md)
- Project constitution (CLAUDE.md)
- Memory system context

**Churn Zone (dynamic suffix):**
- Today's date
- Working directory
- Git status
- Platform info

### Hook Changes

| Hook | Change | Platform Gate |
|------|--------|--------------|
| `hook_session_start.py` | Zone labels on memory context | IS_OPENCODE only |
| `hook_precompact.py` | Gold Prefix analysis + stable summary | IS_OPENCODE only |
| `hook_precompact.py` | `export_transcript()` accepts pre-parsed entries | Both (optimization) |
| `memory.py` | Platform-aware superpowers path | Both |
| `hook_memory_sync.py` | Platform-aware superpowers path | Both |

### Agent Sync

Script: `scripts/sync-agents-to-opencode.py`

Generates `agents/*/SKILL.md` (OpenCode format) from `.claude/agents/*.md` (canonical). Adds `recommended_model` (pro/flash) and `tools` frontmatter fields.

## Success Criteria

- Platform detection correctly identifies both machines
- No Gemini-specific labels appear in Claude Code sessions
- Hooks run without import/path errors on both machines
- Agent sync generates all 30 agents with correct format
- No hardcoded machine-specific paths in shared code
