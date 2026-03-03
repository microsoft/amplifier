# Cross-Platform Global Skills Design Spec

**Date:** 2026-03-03
**Status:** Approved
**Author:** Claude (validated design)

---

## Problem

Amplifier's 27 commands and 36 agents are only available when starting Claude Code from the Amplifier repo (`/opt/amplifier`). When starting from other project repos (e.g., `universal-siem-monorepo`), none of these skills are accessible. Claude Code discovers commands and agents from the working directory's `.claude/` folder, so switching projects loses all Amplifier tooling.

Additionally, the project was originally built for Windows (Git Bash on Windows Server 2025) and contains hardcoded Windows paths throughout commands, tests, and config files. These paths break when running on Ubuntu Linux.

---

## Goal

1. Make all Amplifier skills (commands + agents) available globally across all projects via symlinks into `~/.claude/`.
2. Add cross-platform path resolution so the same codebase works on both Ubuntu Linux and Windows without modification.

---

## Approach

### Skill Portability via Symlinks

A setup script (`scripts/setup-global-skills.sh`) creates symlinks from `~/.claude/commands/` and `~/.claude/agents/` to the corresponding files in the Amplifier repo.

Behavior:
- Backs up existing global files to `~/.claude/backups/YYYY-MM-DD/` before overwriting
- Handles subdirectories (e.g., `commands/ddd/`)
- Idempotent: safe to re-run — skips correct symlinks, refreshes broken ones, does not create duplicate backups
- Auto-detects the Amplifier repo path from the script's own location (`$(dirname "$0")/../..`)

### Cross-Platform Path Resolution

- Environment variable `AMPLIFIER_HOME` is set in the shell profile: `/opt/amplifier` on Linux, `/c/claude/amplifier` on Windows Git Bash
- Shared library `scripts/lib/platform.sh` provides fallback detection when the env var is absent: checks `$AMPLIFIER_HOME` → checks `/opt/amplifier` → checks `/c/claude/amplifier`
- All commands replace hardcoded paths with `$AMPLIFIER_HOME`
- Commands referencing project-specific files (`AGENTS_CATALOG.md`, `docs/specs/`, `docs/plans/`) use "if file exists" fallback logic so they degrade gracefully in non-Amplifier projects

---

## Files Changed

### New Files

| File | Purpose |
|------|---------|
| `scripts/lib/platform.sh` | Shared platform detection library. Detects OS, sets `AMPLIFIER_HOME` via: check `$AMPLIFIER_HOME` env var → check `/opt/amplifier` → check `/c/claude/amplifier`. Sourced by all scripts that need path resolution. |
| `scripts/setup-global-skills.sh` | Setup script. Backs up existing `~/.claude/commands/` and `~/.claude/agents/` files to `~/.claude/backups/YYYY-MM-DD/`. Creates symlinks from `~/.claude/` to Amplifier repo. Handles subdirectories like `commands/ddd/`. Reports what was linked, backed up, or skipped. Idempotent. |

### Commands (2 files)

| File | Change |
|------|--------|
| `.claude/commands/recall.md` | Replace 3x `cd /c/claude/amplifier` with `cd $AMPLIFIER_HOME`. Replace `C:/claude/amplifier/tmp/` with `$AMPLIFIER_HOME/tmp/`. Add platform detection note. |
| `.claude/commands/docs.md` | Replace hardcoded `C:/claude/PROJECT/` paths with dynamic resolution using `$AMPLIFIER_HOME` or project root detection. |

### Project Config (2 files)

| File | Lines | Change |
|------|-------|--------|
| `CLAUDE.md` | 7–9 | Update workspace root, platform description, and safety rules path to be cross-platform with detection note. |
| `COWORK.md` | 16, 18, 135, 143, 164 | Replace Windows paths, PowerShell references, and IIS deployment references with cross-platform equivalents. |

### Tests (3 files)

| File | Change |
|------|--------|
| `tests/hooks/test_guard_paths.sh` | Replace `C:/claude/scripts/` with platform-detected path via `scripts/lib/platform.sh`. |
| `tests/hooks/test_hook_stop.sh` | Replace `C:/claude/amplifier/` with platform-detected path. |
| `tests/hooks/test_session_end_index.sh` | Replace 5x `C:/claude/amplifier` with platform-detected path. |

### Agents (1 file)

| File | Change |
|------|--------|
| `.claude/agents/handoff-gemini.md` | Update Windows path examples to cross-platform equivalents. |

### Platform Detection Tests (1 file)

| File | Change |
|------|--------|
| `.claude/tools/test_platform_detect.py` | Add Linux test cases alongside existing Windows test cases. |

**No changes to historical docs** — specs and plans in `docs/` remain as reference material.

---

## Impact

- All 27 commands and 36 agents become available in every Claude Code session regardless of working directory.
- Re-running the setup script is safe and produces no side effects beyond refreshing stale symlinks.
- Linux CI/CD pipelines and local Linux dev environments can run all tests without modification.
- Windows behavior is preserved — no existing Windows paths or scripts are removed, only augmented with detection logic.
- Projects that lack Amplifier-specific files (`AGENTS_CATALOG.md`, etc.) will degrade gracefully rather than error.

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| Implementation: platform lib | modular-builder | Create `scripts/lib/platform.sh` |
| Implementation: setup script | modular-builder | Create `scripts/setup-global-skills.sh` |
| Implementation: command fixes | modular-builder | Update `recall.md`, `docs.md` with `$AMPLIFIER_HOME` |
| Implementation: config fixes | modular-builder | Update `CLAUDE.md`, `COWORK.md` |
| Implementation: test fixes | modular-builder | Update 3 test scripts + `test_platform_detect.py` |
| Implementation: agent fix | modular-builder | Update `handoff-gemini.md` |
| Verification | test-coverage | Run all tests, verify symlinks work |
| Cleanup | post-task-cleanup | Final hygiene pass |

---

## Test Plan

Each item is a concrete acceptance criterion. The implementation is complete when all pass.

1. **Setup script — initial run:** Execute `scripts/setup-global-skills.sh`. Verify symlinks exist in `~/.claude/commands/` and `~/.claude/agents/` pointing to the correct Amplifier repo files.

2. **Setup script — idempotent:** Run `scripts/setup-global-skills.sh` a second time. Verify: no errors, no duplicate backup directories created, all symlinks remain correct.

3. **Global skill availability:** Start Claude Code from a non-Amplifier project directory (e.g., `/opt/monorepo-workspace/universal-siem-monorepo/`). Verify `/tdd`, `/debug`, `/verify`, and `/commit` are available.

4. **`/recall` path resolution:** Run `/recall` from a non-Amplifier project. Verify `AMPLIFIER_HOME` resolves to `/opt/amplifier` and the command executes without path errors.

5. **`/docs search` path resolution:** Run `/docs search` from a non-Amplifier project. Verify it completes without hardcoded-path errors.

6. **Linux hook tests — guard paths:** Run `tests/hooks/test_guard_paths.sh` on Linux. All assertions pass.

7. **Linux hook tests — session end index:** Run `tests/hooks/test_session_end_index.sh` on Linux. All assertions pass.

8. **Platform detection — Linux:** `scripts/lib/platform.sh` correctly sets `AMPLIFIER_HOME=/opt/amplifier` on Ubuntu Linux when no env var is pre-set.

9. **Platform detection — unit tests:** `uv run pytest .claude/tools/test_platform_detect.py` passes on Linux, including the newly added Linux test cases.

10. **Subdirectory symlinks:** Verify `~/.claude/commands/ddd/` contains symlinks to Amplifier's `commands/ddd/` files.
