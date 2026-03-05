# Cross-Platform Global Skills Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make all Amplifier skills available globally across projects via symlinks, and fix all Windows-hardcoded paths for cross-platform support (Linux + Windows).

**Architecture:** A shared platform detection library (`scripts/lib/platform.sh`) sets `AMPLIFIER_HOME` dynamically. Commands use `$AMPLIFIER_HOME` instead of hardcoded paths. A setup script symlinks all commands and agents to `~/.claude/` for global availability.

**Tech Stack:** Bash (scripts), Markdown (commands/agents), Python (platform_detect.py tests)

**Spec:** `docs/specs/2026-03-03-cross-platform-global-skills-design.md`

---

## Chunk 1: Platform Foundation

### Task 1: Create shared platform detection library

**Agent:** modular-builder

**Files:**
- Create: `scripts/lib/platform.sh`

- [ ] **Step 1: Create the platform detection library**

```bash
#!/bin/bash
# Shared platform detection for Amplifier scripts.
# Source this file: . "$(dirname "$0")/../lib/platform.sh"
# Or from tests: . "$REPO_ROOT/scripts/lib/platform.sh"

# If AMPLIFIER_HOME is already set, respect it
if [ -n "$AMPLIFIER_HOME" ]; then
    return 0 2>/dev/null || true
fi

# Auto-detect based on which path exists
if [ -d "/opt/amplifier" ]; then
    export AMPLIFIER_HOME="/opt/amplifier"
elif [ -d "/c/claude/amplifier" ]; then
    export AMPLIFIER_HOME="/c/claude/amplifier"
elif [ -d "C:/claude/amplifier" ]; then
    export AMPLIFIER_HOME="C:/claude/amplifier"
else
    # Fallback: derive from script location if sourced from within the repo
    _script_dir="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
    if [ -f "$_script_dir/../../CLAUDE.md" ]; then
        export AMPLIFIER_HOME="$(cd "$_script_dir/../.." && pwd)"
    else
        echo "WARNING: Cannot detect AMPLIFIER_HOME. Set it manually." >&2
    fi
    unset _script_dir
fi

# Also export platform identifier
case "$(uname -s)" in
    Linux*)  export AMPLIFIER_PLATFORM="linux" ;;
    MINGW*|MSYS*|CYGWIN*) export AMPLIFIER_PLATFORM="windows" ;;
    Darwin*) export AMPLIFIER_PLATFORM="macos" ;;
    *)       export AMPLIFIER_PLATFORM="unknown" ;;
esac
```

- [ ] **Step 2: Verify the library works on this machine**

Run: `bash -c '. /opt/amplifier/scripts/lib/platform.sh && echo "HOME=$AMPLIFIER_HOME PLATFORM=$AMPLIFIER_PLATFORM"'`
Expected: `HOME=/opt/amplifier PLATFORM=linux`

- [ ] **Step 3: Commit**

```bash
git add scripts/lib/platform.sh
git commit -m "feat: add shared platform detection library

Cross-platform AMPLIFIER_HOME resolution for all scripts.
Detects Linux (/opt/amplifier), Windows (/c/claude/amplifier),
or derives from script location as fallback.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 2: Create global skills setup script

**Agent:** modular-builder

**Files:**
- Create: `scripts/setup-global-skills.sh`

- [ ] **Step 1: Create the setup script**

```bash
#!/bin/bash
# Setup Amplifier skills globally by symlinking commands and agents to ~/.claude/
# Usage: bash scripts/setup-global-skills.sh
# Safe to re-run — idempotent (skips correct symlinks, refreshes broken ones)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
BACKUP_DIR="$HOME/.claude/backups/$(date +%Y-%m-%d)"

LINKED=0
SKIPPED=0
BACKED_UP=0

link_file() {
    local src="$1"
    local dest="$2"

    # Already a correct symlink — skip
    if [ -L "$dest" ] && [ "$(readlink "$dest")" = "$src" ]; then
        SKIPPED=$((SKIPPED + 1))
        return
    fi

    # Existing file (not a symlink, or wrong target) — back up
    if [ -e "$dest" ] || [ -L "$dest" ]; then
        mkdir -p "$BACKUP_DIR"
        local backup_name="$(basename "$dest")"
        # Preserve subdirectory structure in backup
        local rel_dir="$(dirname "${dest#$HOME/.claude/}")"
        mkdir -p "$BACKUP_DIR/$rel_dir"
        mv "$dest" "$BACKUP_DIR/$rel_dir/$backup_name"
        echo "  Backed up: $dest → $BACKUP_DIR/$rel_dir/$backup_name"
        BACKED_UP=$((BACKED_UP + 1))
    fi

    # Create parent directory if needed
    mkdir -p "$(dirname "$dest")"

    ln -s "$src" "$dest"
    LINKED=$((LINKED + 1))
}

echo "=== Amplifier Global Skills Setup ==="
echo "Source: $REPO_ROOT"
echo ""

# Symlink commands (top-level .md files)
echo "Commands:"
mkdir -p "$HOME/.claude/commands"
for src in "$REPO_ROOT/.claude/commands/"*.md; do
    [ -f "$src" ] || continue
    dest="$HOME/.claude/commands/$(basename "$src")"
    link_file "$src" "$dest"
    echo "  ✓ $(basename "$src")"
done

# Symlink command subdirectories (e.g., commands/ddd/)
for dir in "$REPO_ROOT/.claude/commands/"/*/; do
    [ -d "$dir" ] || continue
    dirname_only="$(basename "$dir")"
    mkdir -p "$HOME/.claude/commands/$dirname_only"
    for src in "$dir"*.md; do
        [ -f "$src" ] || continue
        dest="$HOME/.claude/commands/$dirname_only/$(basename "$src")"
        link_file "$src" "$dest"
        echo "  ✓ $dirname_only/$(basename "$src")"
    done
done

# Symlink agents
echo ""
echo "Agents:"
mkdir -p "$HOME/.claude/agents"
for src in "$REPO_ROOT/.claude/agents/"*.md; do
    [ -f "$src" ] || continue
    dest="$HOME/.claude/agents/$(basename "$src")"
    link_file "$src" "$dest"
    echo "  ✓ $(basename "$src")"
done

echo ""
echo "=== Done ==="
echo "Linked: $LINKED | Skipped (already correct): $SKIPPED | Backed up: $BACKED_UP"
[ "$BACKED_UP" -gt 0 ] && echo "Backups at: $BACKUP_DIR"
```

- [ ] **Step 2: Make executable and test**

Run: `chmod +x /opt/amplifier/scripts/setup-global-skills.sh && bash /opt/amplifier/scripts/setup-global-skills.sh`
Expected: All commands and agents symlinked, existing files backed up.

- [ ] **Step 3: Run again to verify idempotent**

Run: `bash /opt/amplifier/scripts/setup-global-skills.sh`
Expected: All items show "Skipped", 0 linked, 0 backed up.

- [ ] **Step 4: Verify symlinks work from another project**

Run: `ls -la ~/.claude/commands/tdd.md ~/.claude/commands/debug.md ~/.claude/agents/zen-architect.md`
Expected: Each shows symlink → `/opt/amplifier/.claude/...`

- [ ] **Step 5: Commit**

```bash
git add scripts/setup-global-skills.sh
git commit -m "feat: add global skills setup script

Symlinks all Amplifier commands and agents to ~/.claude/ for
cross-project availability. Idempotent, backs up existing files.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 2: Fix Command Files

### Task 3: Fix recall.md Windows paths

**Agent:** modular-builder

**Files:**
- Modify: `.claude/commands/recall.md` (lines 31, 48, 61-63, 112)

- [ ] **Step 1: Replace all hardcoded paths**

Make these exact replacements in `.claude/commands/recall.md`:

| Line | Old | New |
|------|-----|-----|
| 31 | `cd /c/claude/amplifier && uv run python scripts/recall/recall_day.py list DATE_EXPR` | `cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall_day.py list DATE_EXPR` |
| 48 | `cd /c/claude/amplifier && uv run python scripts/recall/recall_day.py expand SESSION_ID` | `cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall_day.py expand SESSION_ID` |
| 61 | `cd /c/claude/amplifier && uv run python scripts/recall/recall-search.py "VARIANT_1" -n 5` | `cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall-search.py "VARIANT_1" -n 5` |
| 62 | `cd /c/claude/amplifier && uv run python scripts/recall/recall-search.py "VARIANT_2" -n 5` | `cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall-search.py "VARIANT_2" -n 5` |
| 63 | `cd /c/claude/amplifier && uv run python scripts/recall/recall-search.py "VARIANT_3" -n 5` | `cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall-search.py "VARIANT_3" -n 5` |
| 112 | `cd /c/claude/amplifier && uv run python scripts/recall/session-graph.py DATE_EXPR --no-open -o C:/claude/amplifier/tmp/session-graph.html` | `cd "$AMPLIFIER_HOME" && uv run python scripts/recall/session-graph.py DATE_EXPR --no-open -o "$AMPLIFIER_HOME/tmp/session-graph.html"` |

Also add a platform detection note after the `## Arguments` section (after line 11):

```markdown
## Platform Note

`AMPLIFIER_HOME` must resolve to the Amplifier repo root. Detection order:
1. Environment variable `$AMPLIFIER_HOME` if set
2. `/opt/amplifier` (Linux)
3. `/c/claude/amplifier` (Windows/Git Bash)

If not set, detect before running commands:
```bash
AMPLIFIER_HOME="${AMPLIFIER_HOME:-$([ -d /opt/amplifier ] && echo /opt/amplifier || echo /c/claude/amplifier)}"
```
```

- [ ] **Step 2: Verify recall still works**

Run: `cd /opt/amplifier && AMPLIFIER_HOME=/opt/amplifier uv run python scripts/recall/recall-search.py "test" -n 2`
Expected: Returns search results.

- [ ] **Step 3: Commit**

```bash
git add .claude/commands/recall.md
git commit -m "fix: replace hardcoded Windows paths in recall.md

Use \$AMPLIFIER_HOME for cross-platform path resolution.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 4: Fix docs.md Windows paths

**Agent:** modular-builder

**Files:**
- Modify: `.claude/commands/docs.md` (lines 36-38, 52, 59, 65, 73, 82-96)

- [ ] **Step 1: Replace script invocation paths**

Replace all `cd /c/claude/amplifier` with `cd "$AMPLIFIER_HOME"` on lines 36, 37, 38, 52, 59, 65, 73.

- [ ] **Step 2: Replace project roots mapping (lines 82-96)**

Replace the entire project roots block:

Old (lines 81-96):
```
# Use the path from search results — prepend the project root
cat "C:/claude/PROJECT_NAME/PATH_FROM_RESULT"

Project roots:
- amplifier → `C:/claude/amplifier/`
- fusecp-enterprise → `C:/claude/fusecp-enterprise/`
- universal-siem-monorepo → `C:/claude/universal-siem-monorepo/`
- universal-siem-docs → `C:/claude/universal-siem-docs/`
- universal-siem-agent-aot → `C:/claude/universal-siem-agent-aot/`
- universal-siem-linux-agent → `C:/claude/universal-siem-linux-agent/`
- universal-siem-shared → `C:/claude/universal-siem-shared/`
- psmux → `C:/claude/psmux/`
- webpsmux → `C:/claude/webpsmux/`
- claude-tools → `C:/claude/claude-tools/`
- superpowers → `C:/claude/superpowers/`
```

New:
```
# Use the path from search results — prepend the project root
# Use Read tool instead of cat for reading docs.

# Project roots vary by platform. Detect the parent directory:
# Linux: /opt/ (most projects), /opt/monorepo-workspace/ (siem monorepo)
# Windows: C:/claude/ (all projects)
#
# Common mappings:
# - amplifier → Linux: /opt/amplifier/ | Windows: C:/claude/amplifier/
# - universal-siem-monorepo → Linux: /opt/monorepo-workspace/universal-siem-monorepo/ | Windows: C:/claude/universal-siem-monorepo/
# - universal-siem-docs → Linux: /opt/universal-siem-docs/ | Windows: C:/claude/universal-siem-docs/
# - universal-siem-linux-agent → Linux: /opt/universal-siem-linux-agent/ | Windows: C:/claude/universal-siem-linux-agent/
# - genetics-platform → Linux: /opt/genetics-platform/ | Windows: C:/claude/genetics-platform/
# - webtmux → Linux: /opt/webtmux/ | Windows: C:/claude/webtmux/
#
# For other projects, check /opt/<project>/ (Linux) or C:/claude/<project>/ (Windows).
```

- [ ] **Step 3: Add platform note after Arguments section (same as recall.md)**

Add the same `## Platform Note` section with AMPLIFIER_HOME detection.

- [ ] **Step 4: Verify docs search still works**

Run: `cd /opt/amplifier && uv run python scripts/recall/docs-search.py "authentication" -n 2`
Expected: Returns search results.

- [ ] **Step 5: Commit**

```bash
git add .claude/commands/docs.md
git commit -m "fix: replace hardcoded Windows paths in docs.md

Use \$AMPLIFIER_HOME and cross-platform project root mapping.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 3: Fix Config Files

### Task 5: Fix CLAUDE.md identity section

**Agent:** modular-builder

**Files:**
- Modify: `CLAUDE.md` (lines 7-9)

- [ ] **Step 1: Replace identity section**

Old (lines 7-9):
```
- Workspace root: `C:\claude\amplifier\`
- Platform: Windows Server 2025, Git Bash shell
- Safety rules: See `C:\claude\CLAUDE.md` (path restriction, reserved names, null redirection)
```

New:
```
- Workspace root: Linux: `/opt/amplifier/` | Windows: `C:\claude\amplifier\`
- Platform: Ubuntu Linux (primary), Windows Server 2025 (secondary)
- Safety rules: Linux: `scripts/guard-paths-linux.sh` | Windows: `C:\claude\CLAUDE.md`
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "fix: update CLAUDE.md identity for cross-platform support

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 6: Fix COWORK.md Windows paths

**Agent:** modular-builder

**Files:**
- Modify: `COWORK.md` (lines 16, 18, 135, 146, 149, 160, 164)

- [ ] **Step 1: Update workspace separation table (lines 14-18)**

Old:
```
| `C:\claude\amplifier\` | Shared (git repo) | Source of truth for all code |
| `C:\claude\amplifier\.claude\` | Claude ONLY | Agents, commands, tools, skills |
| `C:\Przemek\` | Gemini ONLY | OPENCODE.md, agents (SKILL.md format), private memory |
```

New:
```
| Linux: `/opt/amplifier/` / Windows: `C:\claude\amplifier\` | Shared (git repo) | Source of truth for all code |
| `<amplifier>/.claude/` | Claude ONLY | Agents, commands, tools, skills |
| `C:\Przemek\` (Windows only) | Gemini ONLY | OPENCODE.md, agents (SKILL.md format), private memory |
```

- [ ] **Step 2: Update PR workflow line (line 135)**

Old: `**Claude reviews/merges PRs** via PowerShell scripts at `C:\claude\scripts\gitea-*.ps1``

New: `**Claude reviews/merges PRs** via bash scripts at `scripts/gitea/gitea-*.sh` (or `tea` CLI directly)`

- [ ] **Step 3: Update safety boundaries (lines 146, 149)**

Line 146 — keep as-is (intentionally Windows: `C:\FuseCP\` production)
Line 149 — keep as-is (intentionally Windows: `C:\Przemek\`)

- [ ] **Step 4: Update agent sync section (lines 160, 164)**

Old line 160: `Gemini copies: `C:\Przemek\agents\<name>\SKILL.md` (OpenCode format)`
New: `Gemini copies: `C:\Przemek\agents\<name>\SKILL.md` (OpenCode format, Windows only)`

Old line 164: `bash /c/Przemek/scripts/sync-agents.sh`
New: `bash "${PRZEMEK_HOME:-/c/Przemek}/scripts/sync-agents.sh"  # Windows only`

- [ ] **Step 5: Commit**

```bash
git add COWORK.md
git commit -m "fix: update COWORK.md paths for cross-platform support

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 4: Fix Test Scripts

### Task 7: Fix test scripts for cross-platform

**Agent:** modular-builder

**Files:**
- Modify: `tests/hooks/test_guard_paths.sh` (line 5)
- Modify: `tests/hooks/test_session_end_index.sh` (lines 5, 23, 33, 51, 62)
- Modify: `tests/hooks/test_hook_stop.sh` (lines 5, 11)

- [ ] **Step 1: Fix test_guard_paths.sh**

Add platform detection at top. Replace line 5:

Old:
```bash
GUARD="C:/claude/scripts/guard-paths.sh"
```

New:
```bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
. "$REPO_ROOT/scripts/lib/platform.sh"

# Use platform-appropriate guard script
if [ "$AMPLIFIER_PLATFORM" = "linux" ]; then
    GUARD="$AMPLIFIER_HOME/scripts/guard-paths-linux.sh"
else
    GUARD="$AMPLIFIER_HOME/scripts/guard-paths.sh"
fi
```

Also update the test cases: on Linux the allowed/blocked paths are different (Linux guard allows `/opt/`, `/home/`, `/tmp/` — not `C:\claude\`). Add a platform conditional:

```bash
if [ "$AMPLIFIER_PLATFORM" = "linux" ]; then
    # Linux test cases
    run_test "Allow Write to /opt/amplifier/test.py" \
        '{"tool_name":"Write","tool_input":{"file_path":"/opt/amplifier/test.py"}}' 0
    run_test "Allow Write to /home/user/file.txt" \
        '{"tool_name":"Write","tool_input":{"file_path":"/home/user/file.txt"}}' 0
    run_test "Block Write to /etc/passwd" \
        '{"tool_name":"Write","tool_input":{"file_path":"/etc/passwd"}}' 2
    run_test "Block Write to /usr/local/file.txt" \
        '{"tool_name":"Write","tool_input":{"file_path":"/usr/local/file.txt"}}' 2
    run_test "Allow Bash mkdir under /opt" \
        '{"tool_name":"Bash","tool_input":{"command":"mkdir -p /opt/amplifier/tmp/test"}}' 0
    run_test "Block Bash mkdir under /etc" \
        '{"tool_name":"Bash","tool_input":{"command":"mkdir /etc/badpath"}}' 2
    run_test "Allow Read tool (passthrough)" \
        '{"tool_name":"Read","tool_input":{"file_path":"/anywhere/file.txt"}}' 0
else
    # Windows test cases (original)
    run_test "Allow Write to C:\\claude\\amplifier\\test.py" \
        '{"tool_name":"Write","tool_input":{"file_path":"C:\\claude\\amplifier\\test.py"}}' 0
    # ... (keep all existing Windows tests)
fi
```

- [ ] **Step 2: Fix test_session_end_index.sh**

Replace the top of the file (lines 1-5) to add platform detection:

Old line 5: `HOOK="C:/claude/amplifier/.claude/hooks/session-end-index.sh"`

New (replace lines 4-5):
```bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
. "$REPO_ROOT/scripts/lib/platform.sh"

HOOK="$AMPLIFIER_HOME/.claude/hooks/session-end-index.sh"
```

Replace all other hardcoded paths:
- Line 23: `"C:/claude/amplifier/$script"` → `"$AMPLIFIER_HOME/$script"`
- Lines 33, 51, 62: `cd /c/claude/amplifier` → `cd "$AMPLIFIER_HOME"`

- [ ] **Step 3: Fix test_hook_stop.sh**

Replace lines 4-5:

Old line 5: `HOOK="C:/claude/amplifier/.claude/tools/hook_stop.py"`

New (replace lines 4-5):
```bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
REPO_ROOT="$(cd "$SCRIPT_DIR/../.." && pwd)"
. "$REPO_ROOT/scripts/lib/platform.sh"

HOOK="$AMPLIFIER_HOME/.claude/tools/hook_stop.py"
```

Old line 11: `cd /c/claude/amplifier`
New: `cd "$AMPLIFIER_HOME"`

- [ ] **Step 4: Run all tests**

Run: `bash tests/hooks/test_session_end_index.sh`
Expected: All PASS

Run: `bash tests/hooks/test_hook_stop.sh`
Expected: All PASS

Run: `bash tests/hooks/test_guard_paths.sh`
Expected: All PASS (using Linux guard script and Linux test cases)

- [ ] **Step 5: Commit**

```bash
git add tests/hooks/test_guard_paths.sh tests/hooks/test_session_end_index.sh tests/hooks/test_hook_stop.sh
git commit -m "fix: make test scripts cross-platform

Source scripts/lib/platform.sh for AMPLIFIER_HOME detection.
Add Linux-specific test cases for guard-paths.

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

## Chunk 5: Fix Agent File + Final Verification

### Task 8: Fix handoff-gemini.md path examples

**Agent:** modular-builder

**Files:**
- Modify: `.claude/agents/handoff-gemini.md` (line 40 area)

- [ ] **Step 1: Add cross-platform note near Windows path examples**

Find the line referencing `C:\claude\fusecp-enterprise` and add a note:

```markdown
> **Path note:** Paths are platform-specific. Linux: `/opt/<repo>/`, Windows: `C:\claude\<repo>\`
```

Do NOT change the IIS deployment references (lines ~220) — those are intentionally Windows-only.

- [ ] **Step 2: Commit**

```bash
git add .claude/agents/handoff-gemini.md
git commit -m "docs: add cross-platform path note to handoff-gemini agent

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

---

### Task 9: Run setup script and verify end-to-end

**Agent:** test-coverage

- [ ] **Step 1: Run the global skills setup**

Run: `bash /opt/amplifier/scripts/setup-global-skills.sh`
Expected: All commands and agents symlinked.

- [ ] **Step 2: Verify key symlinks exist**

Run: `ls -la ~/.claude/commands/brainstorm.md ~/.claude/commands/tdd.md ~/.claude/commands/recall.md ~/.claude/agents/zen-architect.md ~/.claude/agents/modular-builder.md`
Expected: All show symlinks → `/opt/amplifier/.claude/...`

- [ ] **Step 3: Verify /recall works with AMPLIFIER_HOME**

Run: `cd /opt/universal-siem-docs && AMPLIFIER_HOME=/opt/amplifier uv run --project /opt/amplifier python /opt/amplifier/scripts/recall/recall-search.py "authentication" -n 2`
Expected: Returns results (proves scripts work from outside the repo).

- [ ] **Step 4: Verify /docs works with AMPLIFIER_HOME**

Run: `cd /opt/universal-siem-docs && AMPLIFIER_HOME=/opt/amplifier uv run --project /opt/amplifier python /opt/amplifier/scripts/recall/docs-search.py "authentication" -n 2`
Expected: Returns results.

- [ ] **Step 5: Run all test suites**

Run: `bash /opt/amplifier/tests/hooks/test_session_end_index.sh && bash /opt/amplifier/tests/hooks/test_hook_stop.sh && bash /opt/amplifier/tests/hooks/test_guard_paths.sh`
Expected: All PASS.

- [ ] **Step 6: Verify idempotent re-run**

Run: `bash /opt/amplifier/scripts/setup-global-skills.sh`
Expected: 0 linked, all skipped, 0 backed up.

---

### Task 10: Post-task cleanup

**Agent:** post-task-cleanup

- [ ] **Step 1: Check git status for untracked files**

Run: `git status`
Expected: Clean working tree (all changes committed).

- [ ] **Step 2: Verify no Windows paths remain in modified files**

Run: `grep -rn '/c/claude\|C:/claude\|C:\\claude' .claude/commands/recall.md .claude/commands/docs.md CLAUDE.md COWORK.md tests/hooks/`
Expected: Only matches in COWORK.md Windows-specific sections (intentional) and test_guard_paths.sh Windows test branch (intentional).

- [ ] **Step 3: Final commit if any cleanup needed**
