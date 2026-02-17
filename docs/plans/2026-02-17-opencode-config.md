# OpenCode Configuration for Amplifier Cowork — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Configure OpenCode with proper model settings, Amplifier agent registration, context caching activation, and cowork instructions so Gemini can operate as the junior developer.

**Architecture:** Set User env vars for platform detection, create global opencode.json with Gemini 3 Flash model and instructions, update the agent sync script to output OpenCode-native markdown format alongside existing SKILL.md, and fix platform_detect.py to support env-var-based detection (enabling Gold Prefix context caching).

**Tech Stack:** OpenCode v1.2.6, Google Gemini 3 Flash, Bash, Python, JSONC

---

## Task 1: Set Environment Variables

**Agent:** modular-builder
**No TDD needed** (env var setup — nothing to unit test)
**Commit:** N/A (no code changes, system-level change)

### Steps

- [ ] Open an elevated PowerShell session (or use the existing terminal)
- [ ] Set `GOOGLE_API_KEY` as a User-scoped environment variable, reading the key from `C:\Users\Administrator.ERGOLAB\.local\share\opencode\auth.json`:

```powershell
# Read key from auth.json
$auth = Get-Content "C:\Users\Administrator.ERGOLAB\.local\share\opencode\auth.json" | ConvertFrom-Json
$apiKey = $auth.providers.google.api_key   # adjust property path if needed

# Set as User env var (persists across sessions)
[System.Environment]::SetEnvironmentVariable("GOOGLE_API_KEY", $apiKey, "User")
```

- [ ] Set `OPENCODE=1` as a User-scoped environment variable:

```powershell
[System.Environment]::SetEnvironmentVariable("OPENCODE", "1", "User")
```

- [ ] Verify both are set correctly:

```powershell
[System.Environment]::GetEnvironmentVariable("GOOGLE_API_KEY", "User") | Select-Object -First 1
[System.Environment]::GetEnvironmentVariable("OPENCODE", "User")
# Expected: <api_key_value>
# Expected: 1
```

- [ ] Confirm env vars are visible in a new Git Bash shell:

```bash
echo "GOOGLE_API_KEY=${GOOGLE_API_KEY:0:8}..."  # show only prefix for safety
echo "OPENCODE=$OPENCODE"
# Expected: OPENCODE=1
```

**Note:** The `OPENCODE=1` variable is the critical one — it triggers the triple-priority platform detection in Task 3, ensuring hooks activate Gold Prefix context caching when running under OpenCode.

---

## Task 2: Create opencode.json

**Agent:** modular-builder
**No TDD needed** (JSON config file)
**Commit:** N/A (file lives outside the git repo at `~/.config/opencode/`)

### Steps

- [ ] Delete the broken leftover config:

```bash
rm -f "/c/Users/Administrator.ERGOLAB/.config/opencode/opencode-bad.json"
# Verify it's gone:
ls /c/Users/Administrator.ERGOLAB/.config/opencode/
```

- [ ] Create `C:\Users\Administrator.ERGOLAB\.config\opencode\opencode.json` with the following content:

```json
{
  "$schema": "https://opencode.ai/config.json",
  "model": "google/gemini-3-flash-preview",
  "small_model": "google/gemini-2.5-flash-lite",
  "theme": "opencode",
  "autoupdate": true,
  "tui": { "scroll_speed": 3 },
  "tools": { "write": true, "edit": true, "bash": true },
  "permission": { "edit": "allow", "bash": "ask", "webfetch": "allow" },
  "instructions": [
    "C:\\Przemek\\OPENCODE.md",
    "AGENTS.md",
    "COWORK.md"
  ],
  "provider": {
    "google": {
      "options": {
        "timeout": 600000
      }
    }
  },
  "mcp": {
    "chrome-devtools": {
      "type": "local",
      "command": [
        "node",
        "C:\\Przemek\\chrome-devtools-mcp\\node_modules\\chrome-devtools-mcp\\build\\src\\index.js"
      ],
      "enabled": true
    }
  }
}
```

- [ ] Verify OpenCode reads the config correctly:

```bash
opencode debug config
# Expected output includes:
#   model: google/gemini-3-flash-preview
#   instructions: [C:\Przemek\OPENCODE.md, AGENTS.md, COWORK.md]
```

- [ ] Confirm the config directory now contains only `opencode.json` (no stale files):

```bash
ls /c/Users/Administrator.ERGOLAB/.config/opencode/
# Expected: agents/  opencode.json
```

**Instructions path note:** `AGENTS.md` and `COWORK.md` are relative paths — OpenCode resolves them relative to the working directory when launched. Gemini should always `cd C:\claude\amplifier` before starting OpenCode so these resolve correctly.

---

## Task 3: Fix platform_detect.py

**Agent:** modular-builder
**TDD:** Yes — write test first, then fix implementation
**File:** `C:\claude\amplifier\.claude\tools\platform_detect.py`
**Commit:** Yes (to git on main)

### Steps

#### 3a. Write the test first

- [ ] Create test file `C:\claude\amplifier\.claude\tools\test_platform_detect.py`:

```python
"""
Tests for platform_detect.py — env var priority detection.

Run with: python .claude/tools/test_platform_detect.py
"""

import os
import sys
import importlib
import unittest


def reload_detect(env_overrides: dict) -> object:
    """Reload platform_detect with the given env vars patched."""
    saved = {}
    for k, v in env_overrides.items():
        saved[k] = os.environ.get(k)
        if v is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = v

    # Force module reload so top-level constants are re-evaluated
    if "platform_detect" in sys.modules:
        del sys.modules["platform_detect"]

    # Add tools dir to path if needed
    tools_dir = os.path.dirname(os.path.abspath(__file__))
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)

    import platform_detect as mod

    # Restore env
    for k, orig in saved.items():
        if orig is None:
            os.environ.pop(k, None)
        else:
            os.environ[k] = orig

    return mod


class TestPlatformDetect(unittest.TestCase):

    def test_claudecode_env_takes_priority(self):
        """CLAUDECODE=1 wins even if OPENCODE=1 is also set."""
        mod = reload_detect({"CLAUDECODE": "1", "OPENCODE": "1"})
        self.assertTrue(mod.IS_CLAUDE_CODE, "CLAUDECODE=1 should set IS_CLAUDE_CODE=True")
        self.assertFalse(mod.IS_OPENCODE, "CLAUDECODE=1 should set IS_OPENCODE=False")

    def test_opencode_env_activates_opencode(self):
        """OPENCODE=1 (with no CLAUDECODE) should set IS_OPENCODE=True."""
        mod = reload_detect({"CLAUDECODE": None, "OPENCODE": "1"})
        self.assertFalse(mod.IS_CLAUDE_CODE, "OPENCODE=1 alone should not set IS_CLAUDE_CODE")
        self.assertTrue(mod.IS_OPENCODE, "OPENCODE=1 should set IS_OPENCODE=True")

    def test_no_env_vars_falls_back_to_directory(self):
        """Without env vars, falls back to directory-based detection."""
        mod = reload_detect({"CLAUDECODE": None, "OPENCODE": None})
        # On this machine both dirs exist, so IS_CLAUDE_CODE should be True
        # (directory detection: C:/claude/amplifier exists)
        # Just verify the module loads without error and returns booleans
        self.assertIsInstance(mod.IS_CLAUDE_CODE, bool)
        self.assertIsInstance(mod.IS_OPENCODE, bool)

    def test_opencode_env_sets_correct_root(self):
        """OPENCODE=1 should set AMPLIFIER_ROOT to C:/Przemek."""
        mod = reload_detect({"CLAUDECODE": None, "OPENCODE": "1"})
        self.assertEqual(mod.AMPLIFIER_ROOT, "C:/Przemek")

    def test_claudecode_env_sets_correct_root(self):
        """CLAUDECODE=1 should set AMPLIFIER_ROOT to C:/claude."""
        mod = reload_detect({"CLAUDECODE": "1", "OPENCODE": None})
        self.assertEqual(mod.AMPLIFIER_ROOT, "C:/claude")


if __name__ == "__main__":
    unittest.main(verbosity=2)
```

- [ ] Run the test — it should FAIL (current implementation lacks env var support):

```bash
cd /c/claude/amplifier
python .claude/tools/test_platform_detect.py
# Expected: FAIL on test_opencode_env_activates_opencode
```

#### 3b. Fix the implementation

- [ ] Replace the detection logic in `C:\claude\amplifier\.claude\tools\platform_detect.py` with the triple-priority approach:

```python
"""
Platform detection for dual-machine Amplifier deployment.

Detects whether we're running on the Claude Code machine (C:/claude/)
or the Gemini/OpenCode machine (C:/Przemek/) and exports path constants
that all hooks use instead of hardcoded paths.

Detection priority (highest to lowest):
  1. CLAUDECODE=1 env var  — set by .bash_profile for Claude Code sessions
  2. OPENCODE=1 env var    — set as User env var for OpenCode sessions
  3. Directory presence    — fallback for environments without env vars set
"""

import os

# Priority 1 & 2: env var detection (explicit, reliable, no ambiguity)
_claudecode_env = os.environ.get("CLAUDECODE") == "1"
_opencode_env = os.environ.get("OPENCODE") == "1"

if _claudecode_env:
    IS_CLAUDE_CODE = True
    IS_OPENCODE = False
elif _opencode_env:
    IS_CLAUDE_CODE = False
    IS_OPENCODE = True
else:
    # Priority 3: directory-based fallback (original behavior)
    IS_CLAUDE_CODE = os.path.isdir("C:/claude/amplifier")
    IS_OPENCODE = os.path.isdir("C:/Przemek") and not IS_CLAUDE_CODE

# Path constants
if IS_CLAUDE_CODE:
    AMPLIFIER_ROOT = "C:/claude"
    SUPERPOWERS_FALLBACK = "C:/claude/superpowers"
elif IS_OPENCODE:
    AMPLIFIER_ROOT = "C:/Przemek"
    SUPERPOWERS_FALLBACK = "C:/Przemek/superpowers"
else:
    # Unknown platform — use home directory fallback
    AMPLIFIER_ROOT = os.path.expanduser("~")
    SUPERPOWERS_FALLBACK = ""


if __name__ == "__main__":
    print(f"IS_CLAUDE_CODE={IS_CLAUDE_CODE}")
    print(f"IS_OPENCODE={IS_OPENCODE}")
    print(f"AMPLIFIER_ROOT={AMPLIFIER_ROOT}")
    print(f"SUPERPOWERS_FALLBACK={SUPERPOWERS_FALLBACK}")
```

#### 3c. Verify tests pass

- [ ] Run tests again — all 5 should pass:

```bash
cd /c/claude/amplifier
python .claude/tools/test_platform_detect.py
# Expected:
# test_claudecode_env_takes_priority ... ok
# test_claudecode_env_sets_correct_root ... ok
# test_no_env_vars_falls_back_to_directory ... ok
# test_opencode_env_activates_opencode ... ok
# test_opencode_env_sets_correct_root ... ok
# ----------------------------------------------------------------------
# Ran 5 tests in 0.001s
# OK
```

- [ ] Quick manual verification with env var override:

```bash
OPENCODE=1 python .claude/tools/platform_detect.py
# Expected:
# IS_CLAUDE_CODE=False
# IS_OPENCODE=True
# AMPLIFIER_ROOT=C:/Przemek
# SUPERPOWERS_FALLBACK=C:/Przemek/superpowers

CLAUDECODE=1 python .claude/tools/platform_detect.py
# Expected:
# IS_CLAUDE_CODE=True
# IS_OPENCODE=False
# AMPLIFIER_ROOT=C:/claude
# SUPERPOWERS_FALLBACK=C:/claude/superpowers
```

#### 3d. Commit

- [ ] Stage and commit both files:

```bash
cd /c/claude/amplifier
git add .claude/tools/platform_detect.py .claude/tools/test_platform_detect.py
git commit -m "fix: triple-priority platform detection (env var > directory)

Add CLAUDECODE and OPENCODE env var support to platform_detect.py so
hooks correctly identify the running platform even when both C:/claude/
and C:/Przemek/ exist on the same machine.

Also adds test_platform_detect.py with 5 unit tests covering all
priority combinations.

🤖 Generated with [Amplifier](https://github.com/microsoft/amplifier)

Co-Authored-By: Amplifier <240397093+microsoft-amplifier@users.noreply.github.com>"
```

---

## Task 4: Update sync-agents.sh

**Agent:** modular-builder
**TDD:** Dry-run verification (not unit tests — bash script)
**File:** `C:\Przemek\scripts\sync-agents.sh`
**Commit:** Yes (to git on main — this file lives in the Amplifier repo tracked via Gemini's workspace)

### Overview

The current script outputs `C:\Przemek\agents\<name>\SKILL.md` (used by custom agent loading). We need to ALSO output `~/.config/opencode/agents/<name>.md` flat files in OpenCode-native frontmatter format so OpenCode's built-in agent discovery finds them.

**Key differences between formats:**

| Field | SKILL.md format | OpenCode native format |
|-------|----------------|----------------------|
| Model field | `recommended_model: flash` | `model: google/gemini-2.5-flash` |
| Mode | not present | `mode: subagent` |
| Tools | not present | `tools: { write: false, edit: false, bash: true }` |
| Location | `C:\Przemek\agents\<name>\SKILL.md` | `~/.config/opencode/agents/<name>.md` |

### Steps

#### 4a. Add the OpenCode output section to sync-agents.sh

- [ ] Replace the contents of `C:\Przemek\scripts\sync-agents.sh` with the updated version below. The new script adds:
  - `OPENCODE_AGENTS_DIR` target variable
  - `MODEL_ID_MAP` mapping tier → full Google model ID
  - `TOOLS_MAP` per agent (write/edit/bash booleans)
  - A second output loop writing flat OpenCode `.md` files
  - Keeps the existing SKILL.md output loop unchanged

```bash
#!/usr/bin/env bash
# sync-agents.sh — Sync Claude Code agents to two formats:
#   1. C:\Przemek\agents\<name>\SKILL.md  (original SKILL.md format)
#   2. ~/.config/opencode/agents/<name>.md (OpenCode native flat format)
# Source: .claude/agents/*.md
# Usage: bash /c/Przemek/scripts/sync-agents.sh
# Idempotent — safe to re-run.

set -uo pipefail

SOURCE_DIR="/c/claude/amplifier/.claude/agents"
TARGET_DIR="/c/Przemek/agents"
OPENCODE_AGENTS_DIR="$HOME/.config/opencode/agents"

# ─── Tier assignments ───────────────────────────────────────────────────────
declare -A TIERS=(
  [agentic-search]="primary"       [bug-hunter]="primary"
  [modular-builder]="primary"      [test-coverage]="primary"
  [content-researcher]="primary"   [analysis-engine]="primary"
  [post-task-cleanup]="primary"    [performance-optimizer]="primary"
  [zen-architect]="senior-review"  [api-contract-designer]="senior-review"
  [database-architect]="senior-review" [security-guardian]="senior-review"
  [contract-spec-author]="senior-review" [subagent-architect]="senior-review"
  [integration-specialist]="senior-review" [module-intent-architect]="senior-review"
  [art-director]="design-specialist"      [component-designer]="design-specialist"
  [design-system-architect]="design-specialist" [layout-architect]="design-specialist"
  [animation-choreographer]="design-specialist" [responsive-strategist]="design-specialist"
  [voice-strategist]="design-specialist"
  [amplifier-expert]="knowledge"         [amplifier-cli-architect]="knowledge"
  [concept-extractor]="knowledge"        [graph-builder]="knowledge"
  [insight-synthesizer]="knowledge"      [knowledge-archaeologist]="knowledge"
  [pattern-emergence]="knowledge"        [visualization-architect]="knowledge"
  [ambiguity-guardian]="knowledge"
)

# ─── Model mappings ──────────────────────────────────────────────────────────
# SKILL.md format (short names)
declare -A MODEL_MAP=(
  [primary]="flash"  [senior-review]="pro"
  [design-specialist]="pro"  [knowledge]="flash"
)

# OpenCode format (full Google model IDs)
declare -A MODEL_ID_MAP=(
  [primary]="google/gemini-2.5-flash"
  [senior-review]="google/gemini-2.5-pro"
  [design-specialist]="google/gemini-2.5-pro"
  [knowledge]="google/gemini-2.5-flash"
)

# ─── Tool permissions per agent (write edit bash) ────────────────────────────
# Format: "write_bool edit_bool bash_bool"
declare -A TOOLS_MAP=(
  # Read-only agents
  [agentic-search]="false false true"
  [analysis-engine]="false false true"

  # Implementation agents (full access)
  [modular-builder]="true true true"
  [bug-hunter]="true true true"
  [component-designer]="true true true"
  [integration-specialist]="true true true"
  [animation-choreographer]="true true true"
  [performance-optimizer]="true true true"

  # Knowledge agents (no file writes)
  [concept-extractor]="false false false"
  [graph-builder]="false false false"
  [insight-synthesizer]="false false false"
  [knowledge-archaeologist]="false false false"
  [pattern-emergence]="false false false"
  [visualization-architect]="false false false"
  [ambiguity-guardian]="false false false"

  # Review agents (bash for checking, no writes)
  [zen-architect]="false false true"
  [api-contract-designer]="false false true"
  [database-architect]="false false true"
  [security-guardian]="false false true"
  [contract-spec-author]="false false true"
  [subagent-architect]="false false true"
  [module-intent-architect]="false false true"

  # Design agents (no file access)
  [art-director]="false false false"
  [design-system-architect]="false false false"
  [layout-architect]="false false false"
  [responsive-strategist]="false false false"
  [voice-strategist]="false false false"

  # Utility agents
  [post-task-cleanup]="true false true"
  [content-researcher]="true false true"
  [amplifier-expert]="true false true"
  [amplifier-cli-architect]="true false true"

  # Test agents
  [test-coverage]="false false true"
)

# ─── Cowork boundary reminder (appended to SKILL.md) ─────────────────────────
JUNIOR_REMINDER='

## Cowork Boundaries (ALWAYS ENFORCE)

You are operating as a JUNIOR DEVELOPER agent under Gemini/OpenCode.
- NEVER suggest modifying `.claude/` directory
- NEVER suggest deploying to IIS or touching `C:\FuseCP\`
- NEVER suggest merging to main or force-pushing
- If a task requires senior-level decisions, flag it and stop
- Always work on feature/* or gemini/* branches'

# ─── Ensure output dirs exist ─────────────────────────────────────────────────
mkdir -p "$TARGET_DIR"
mkdir -p "$OPENCODE_AGENTS_DIR"

count=0
oc_count=0

echo "=== Agent Sync: .claude/agents/ → two targets ==="
echo "  SKILL.md target:  $TARGET_DIR"
echo "  OpenCode target:  $OPENCODE_AGENTS_DIR"
echo ""

for agent_file in "$SOURCE_DIR"/*.md; do
  [[ -f "$agent_file" ]] || continue

  agent_name=$(basename "$agent_file" .md)
  tier="${TIERS[$agent_name]:-knowledge}"
  model="${MODEL_MAP[$tier]:-flash}"
  model_id="${MODEL_ID_MAP[$tier]:-google/gemini-2.5-flash}"
  tools_str="${TOOLS_MAP[$agent_name]:-false false false}"

  # Parse tools string into individual vars
  read -r t_write t_edit t_bash <<< "$tools_str"

  # ── OUTPUT 1: SKILL.md (original format, unchanged) ──────────────────────
  agent_dir="$TARGET_DIR/$agent_name"
  skill_file="$agent_dir/SKILL.md"
  mkdir -p "$agent_dir"

  first_line=$(head -1 "$agent_file")
  if [[ "$first_line" == "---" ]]; then
    frontmatter=$(awk 'BEGIN{found=0} /^---$/{found++; if(found==2) exit; next} found==1{print}' "$agent_file")
    body=$(awk 'BEGIN{found=0} /^---$/{found++; next} found>=2{print}' "$agent_file")

    new_fm=""
    if echo "$frontmatter" | grep -q "^recommended_model:"; then
      new_fm="$frontmatter"
    else
      new_fm="recommended_model: $model
$frontmatter"
    fi

    if ! echo "$new_fm" | grep -q "^tier:"; then
      new_fm="$new_fm
tier: $tier"
    fi

    {
      echo "---"
      echo "$new_fm"
      echo "---"
      echo "$body"
      echo "$JUNIOR_REMINDER"
    } > "$skill_file"
  else
    {
      echo "---"
      echo "recommended_model: $model"
      echo "name: $agent_name"
      echo "description: Agent $agent_name (imported from Claude Code)"
      echo "tier: $tier"
      echo "---"
      echo ""
      cat "$agent_file"
      echo "$JUNIOR_REMINDER"
    } > "$skill_file"
  fi
  ((count++)) || true

  # ── OUTPUT 2: OpenCode native flat .md ───────────────────────────────────
  oc_file="$OPENCODE_AGENTS_DIR/${agent_name}.md"

  # Extract description from frontmatter (first "description:" value)
  if [[ "$first_line" == "---" ]]; then
    frontmatter=$(awk 'BEGIN{found=0} /^---$/{found++; if(found==2) exit; next} found==1{print}' "$agent_file")
    body=$(awk 'BEGIN{found=0} /^---$/{found++; next} found>=2{print}' "$agent_file")
    # Get description — handles single-line and block scalar (take first non-empty line after "description:")
    description=$(echo "$frontmatter" | awk '
      /^description:/ {
        # Check if value is on the same line
        sub(/^description:[[:space:]]*/, "")
        if ($0 != "" && $0 != "|") { print; exit }
        in_desc = 1; next
      }
      in_desc && /^[[:space:]]+/ { sub(/^[[:space:]]+/, ""); print; exit }
      in_desc && /^[^[:space:]]/ { exit }
    ')
  else
    description="Agent $agent_name"
    body=$(cat "$agent_file")
  fi

  # Truncate description to one line for frontmatter
  description_oneline=$(echo "$description" | head -1 | tr -d '\n')

  {
    echo "---"
    echo "name: $agent_name"
    echo "description: \"$description_oneline\""
    echo "mode: subagent"
    echo "model: $model_id"
    echo "tools:"
    echo "  write: $t_write"
    echo "  edit: $t_edit"
    echo "  bash: $t_bash"
    echo "---"
    echo ""
    echo "$body"
    echo "$JUNIOR_REMINDER"
  } > "$oc_file"
  ((oc_count++)) || true

  echo "  [OK] $agent_name (tier: $tier | SKILL: $model | OpenCode: $model_id | tools: write=$t_write edit=$t_edit bash=$t_bash)"
done

echo ""
echo "=== Sync complete ==="
echo "  SKILL.md files: $count  →  $TARGET_DIR"
echo "  OpenCode files: $oc_count  →  $OPENCODE_AGENTS_DIR"
```

#### 4b. Verify script syntax

- [ ] Check bash syntax without running:

```bash
bash -n /c/Przemek/scripts/sync-agents.sh
# Expected: (no output = syntax OK)
```

#### 4c. Test with a single agent (dry run simulation)

- [ ] Run against just one agent to validate output format:

```bash
# Temporarily test on a single agent by running the script with env var override
# Then inspect both output files
bash /c/Przemek/scripts/sync-agents.sh 2>&1 | head -5
# Expected first lines:
# === Agent Sync: .claude/agents/ → two targets ===
#   SKILL.md target:  /c/Przemek/agents
#   OpenCode target:  /root/.config/opencode/agents  (or Windows equivalent)
```

- [ ] Spot-check the OpenCode output for `modular-builder`:

```bash
cat "$HOME/.config/opencode/agents/modular-builder.md" | head -15
# Expected:
# ---
# name: modular-builder
# description: "Primary implementation agent that builds code from specifications."
# mode: subagent
# model: google/gemini-2.5-flash
# tools:
#   write: true
#   edit: true
#   bash: true
# ---
```

- [ ] Spot-check the OpenCode output for `zen-architect` (review tier = pro model, no writes):

```bash
cat "$HOME/.config/opencode/agents/zen-architect.md" | head -12
# Expected:
# ---
# name: zen-architect
# description: "..."
# mode: subagent
# model: google/gemini-2.5-pro
# tools:
#   write: false
#   edit: false
#   bash: true
# ---
```

#### 4d. Commit

- [ ] Commit the updated sync script:

```bash
cd /c/claude/amplifier
# sync-agents.sh lives in C:\Przemek\scripts\ — but we track it if it's symlinked or copied
# If not tracked in this repo, commit wherever it IS tracked:
git add /c/Przemek/scripts/sync-agents.sh 2>/dev/null || true
git status
# If it's not in this repo, the script change is committed from Gemini's workspace
```

**Note:** If `sync-agents.sh` is not tracked in the Amplifier repo (it lives in `C:\Przemek\scripts\`), no git commit is needed here — the file change is already saved. Confirm its tracking status with `git ls-files /c/Przemek/scripts/sync-agents.sh`.

---

## Task 5: Run Sync and Verify Agents

**Agent:** modular-builder
**No TDD** (verification only)
**Commit:** N/A (generated files outside repo)

### Steps

- [ ] Run the full sync:

```bash
bash /c/Przemek/scripts/sync-agents.sh
# Expected: ~32 lines of [OK] entries followed by:
# === Sync complete ===
#   SKILL.md files: 32  →  /c/Przemek/agents
#   OpenCode files: 32  →  /home/.../.config/opencode/agents
```

- [ ] Count OpenCode agent files created:

```bash
ls "$HOME/.config/opencode/agents/" | wc -l
# Expected: 32 (or however many .md files are in .claude/agents/)
```

- [ ] Verify no file is zero-byte (all have content):

```bash
find "$HOME/.config/opencode/agents/" -name "*.md" -empty
# Expected: (no output — no empty files)
```

- [ ] Verify OpenCode discovers the agents:

```bash
opencode agent list
# Expected: list includes built-in OpenCode agents PLUS all 32 Amplifier agents
# Look for: modular-builder, zen-architect, bug-hunter, test-coverage, etc.
```

- [ ] Cross-check that `mode: subagent` is present in every OpenCode agent file:

```bash
grep -L "mode: subagent" "$HOME/.config/opencode/agents/"*.md
# Expected: (no output — all files contain mode: subagent)
```

- [ ] Cross-check that no OpenCode file uses the short model names (should use full IDs):

```bash
grep -l "model: flash\|model: pro" "$HOME/.config/opencode/agents/"*.md
# Expected: (no output — all files use google/gemini-2.5-* format)
```

---

## Task 6: End-to-End Verification

**Agent:** test-coverage
**No commit** (verification only)

### Steps

#### 6a. Platform detection verification

- [ ] Verify all four env var combinations return correct results:

```bash
cd /c/claude/amplifier

# Case 1: CLAUDECODE wins over OPENCODE
CLAUDECODE=1 OPENCODE=1 python .claude/tools/platform_detect.py
# Expected: IS_CLAUDE_CODE=True, IS_OPENCODE=False

# Case 2: OPENCODE alone activates OpenCode mode
CLAUDECODE="" OPENCODE=1 python .claude/tools/platform_detect.py
# Expected: IS_CLAUDE_CODE=False, IS_OPENCODE=True, AMPLIFIER_ROOT=C:/Przemek

# Case 3: CLAUDECODE alone activates Claude Code mode
CLAUDECODE=1 OPENCODE="" python .claude/tools/platform_detect.py
# Expected: IS_CLAUDE_CODE=True, IS_OPENCODE=False, AMPLIFIER_ROOT=C:/claude

# Case 4: No env vars — falls back to directory detection
# (On this machine C:/claude/amplifier exists, so IS_CLAUDE_CODE=True)
python .claude/tools/platform_detect.py
# Expected: IS_CLAUDE_CODE=True (directory-based)
```

- [ ] Run the full unit test suite:

```bash
python .claude/tools/test_platform_detect.py -v
# Expected: Ran 5 tests in <t>s — OK
```

#### 6b. OpenCode config verification

- [ ] Check OpenCode reads the config:

```bash
opencode debug config 2>&1 | grep -E "model|instructions|theme"
# Expected lines containing:
#   model: google/gemini-3-flash-preview
#   instructions: [...]
#   theme: opencode
```

- [ ] Confirm the bad config is gone:

```bash
ls "$HOME/.config/opencode/opencode-bad.json" 2>&1
# Expected: No such file or directory
```

#### 6c. Agent discovery verification

- [ ] Full agent list showing Amplifier subagents are registered:

```bash
opencode agent list 2>&1 | grep -E "modular-builder|zen-architect|bug-hunter|test-coverage|security-guardian"
# Expected: all 5 names appear in the output
```

- [ ] Verify a pro-tier agent has the correct model:

```bash
head -10 "$HOME/.config/opencode/agents/zen-architect.md"
# Expected: model: google/gemini-2.5-pro
```

- [ ] Verify a flash-tier agent has the correct model:

```bash
head -10 "$HOME/.config/opencode/agents/modular-builder.md"
# Expected: model: google/gemini-2.5-flash
```

#### 6d. Live OpenCode session test

- [ ] Start a brief OpenCode session from the Amplifier directory and verify identity/instructions load:

```bash
cd /c/claude/amplifier
# Run a one-shot query (non-interactive)
opencode run "In one sentence: what is your role in this cowork setup, and who is your senior partner?"
# Expected: Response mentions "junior developer", "Gemini", and "Claude Code" or "senior"
```

- [ ] Verify Gold Prefix context caching is active (hooks use IS_OPENCODE=True):

```bash
# The OPENCODE=1 User env var (set in Task 1) means hooks will see IS_OPENCODE=True
# Verify by checking what platform_detect returns in a new shell:
OPENCODE=1 python /c/claude/amplifier/.claude/tools/platform_detect.py
# Expected:
# IS_CLAUDE_CODE=False
# IS_OPENCODE=True
# AMPLIFIER_ROOT=C:/Przemek
```

#### 6e. Summary checklist

- [ ] GOOGLE_API_KEY User env var set
- [ ] OPENCODE=1 User env var set
- [ ] `~/.config/opencode/opencode.json` exists with correct model
- [ ] `~/.config/opencode/opencode-bad.json` deleted
- [ ] `platform_detect.py` uses triple-priority detection
- [ ] `test_platform_detect.py` passes all 5 tests
- [ ] `sync-agents.sh` outputs both SKILL.md and OpenCode flat format
- [ ] 32 `.md` files in `~/.config/opencode/agents/`
- [ ] `opencode agent list` shows all Amplifier agents
- [ ] Live OpenCode session confirms OPENCODE.md identity is loaded

---

## Files Changed Summary

| File | Action | Task |
|------|--------|------|
| `GOOGLE_API_KEY` env var | SET (User scope) | Task 1 |
| `OPENCODE` env var | SET (User scope, value=1) | Task 1 |
| `~/.config/opencode/opencode.json` | CREATE | Task 2 |
| `~/.config/opencode/opencode-bad.json` | DELETE | Task 2 |
| `C:\claude\amplifier\.claude\tools\platform_detect.py` | MODIFY | Task 3 |
| `C:\claude\amplifier\.claude\tools\test_platform_detect.py` | CREATE | Task 3 |
| `C:\Przemek\scripts\sync-agents.sh` | MODIFY | Task 4 |
| `~/.config/opencode/agents/*.md` | CREATE (32 files) | Task 5 |
