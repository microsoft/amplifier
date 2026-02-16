# Dual-Platform Architecture: Claude Code + OpenCode/Gemini

**Date:** 2026-02-15 (updated 2026-02-16)
**Status:** Active
**Decision:** Runtime-gated platform features on single `main` branch

## Overview

Amplifier runs on two AI platforms from a single codebase:

| Platform | Machine | Root Path | AI Model | Detection |
|----------|---------|-----------|----------|-----------|
| **Claude Code** | FUSECP | `C:/claude/amplifier` | Claude Opus 4.6 | `IS_CLAUDE_CODE=True` |
| **OpenCode** | Gemini machine | `C:/Przemek` | Gemini 3 | `IS_OPENCODE=True` |

Both platforms are used daily. All platform-specific code lives on `main` and is gated by runtime checks — no separate branches.

## Architecture Decision

**Considered approaches:**

1. **Separate branches** — `main` for Claude Code, `feature/gemini-opencode` for Gemini. Rejected: creates unacceptable drift since both platforms are active daily and hook files (the files that differ) change frequently.

2. **Runtime gating on main** (chosen) — All code on `main`, Gemini features gated by `if IS_OPENCODE:`. Zero maintenance burden, changes automatically propagate to both platforms.

3. **Overlay directory** — Gemini code in a separate folder, deploy script merges at runtime. Rejected: adds deployment complexity without clear benefit over runtime gating.

## Platform Detection

**Module:** `.claude/tools/platform_detect.py`

```python
IS_CLAUDE_CODE = os.path.isdir("C:/claude/amplifier")
IS_OPENCODE = os.path.isdir("C:/Przemek") and not IS_CLAUDE_CODE
```

**Exports used by hooks:**

| Export | Purpose | Used by |
|--------|---------|---------|
| `IS_CLAUDE_CODE` | Gate Claude-only features | (reserved for future use) |
| `IS_OPENCODE` | Gate Gemini-only features | hook_session_start, hook_precompact |
| `AMPLIFIER_ROOT` | Machine-specific root path | (available for hooks) |
| `SUPERPOWERS_FALLBACK` | Fallback git-notes directory | memory.py, hook_memory_sync, hook_precompact |

## Gemini-Specific Features

### Gold Prefix Context Caching

**Problem:** Gemini 3 uses prefix-based context caching. Dynamic content (date, git status) at the start of the prompt invalidates the cache every session, wasting TPM quota.

**Solution:** Restructure hook output into two zones:

**Frozen Zone (stable prefix)** — Content that rarely changes:
- Core identity and mandates
- Agent manifest
- Project constitution (CLAUDE.md)
- Memory system context

**Churn Zone (dynamic suffix)** — Content that changes every session:
- Today's date
- Working directory
- Git status
- Platform info

**Implementation:**

| Hook | Gemini Feature | Guard |
|------|---------------|-------|
| `hook_session_start.py` | `[FROZEN ZONE]` / `[CHURN ZONE]` labels on memory output | `if IS_OPENCODE:` |
| `hook_precompact.py` | `GoldPrefixCompactor` class — analyzes transcript for stable prefix | `if IS_OPENCODE:` |
| `hook_precompact.py` | Gold Prefix metadata in export header | `if IS_OPENCODE:` |

**On Claude Code:** None of this executes. The `else` branches produce standard headers without zone labels.

### Agent Sync to OpenCode Format

**Script:** `scripts/sync-agents-to-opencode.py`

OpenCode uses a different agent format (`agents/*/SKILL.md`) than Claude Code (`.claude/agents/*.md`). This script generates the OpenCode format from the canonical Claude Code definitions.

**What it adds:**
- `recommended_model`: `pro` (design/architecture agents) or `flash` (implementation/utility agents)
- `tools`: OpenCode tool access list

**Usage:**
```bash
python scripts/sync-agents-to-opencode.py          # Generate all 30 agents
python scripts/sync-agents-to-opencode.py --dry-run # Preview without writing
```

**Run after:** Any change to `.claude/agents/*.md` files.

## Shared Features (Both Platforms)

These features benefit both platforms and are not gated:

| Feature | File | Purpose |
|---------|------|---------|
| `SUPERPOWERS_FALLBACK` path | platform_detect.py | Machine-aware git-notes directory |
| Pre-parsed transcript entries | hook_precompact.py | Avoids double-parsing in export |
| `push_memory_notes()` | hook_precompact.py | Git-notes sync before compaction |

## How to Maintain

### Adding a new hook or modifying an existing one

1. Write the feature for both platforms (or Claude Code only if not relevant to Gemini)
2. If Gemini needs different behavior, add `if IS_OPENCODE:` / `else:` guard
3. The Gemini path never executes on the Claude Code machine — no runtime cost

### Adding a new agent

1. Create `.claude/agents/agent-name.md` (canonical source)
2. Run `python scripts/sync-agents-to-opencode.py` to generate OpenCode format
3. Add the agent to `MODEL_MAP` in the sync script (pro or flash)
4. Update `.claude/AGENTS_CATALOG.md`

### Testing platform detection

```bash
# On Claude Code machine:
uv run python .claude/tools/platform_detect.py
# → IS_CLAUDE_CODE=True, IS_OPENCODE=False

# On OpenCode machine:
python .claude/tools/platform_detect.py
# → IS_CLAUDE_CODE=False, IS_OPENCODE=True
```

## File Index

| File | Platform | Purpose |
|------|----------|---------|
| `.claude/tools/platform_detect.py` | Both | Runtime platform detection |
| `.claude/tools/hook_session_start.py` | Both (gated) | Memory retrieval + zone labels |
| `.claude/tools/hook_precompact.py` | Both (gated) | Transcript export + Gold Prefix |
| `.claude/tools/hook_memory_sync.py` | Both | Git-notes memory sync |
| `.claude/tools/memory.py` | Both | Git-notes memory wrapper |
| `scripts/sync-agents-to-opencode.py` | OpenCode only | Agent format converter |
| `docs/superpowers/specs/this-file.md` | Reference | This documentation |
