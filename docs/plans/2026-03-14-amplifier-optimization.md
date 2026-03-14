# Amplifier Project Optimization Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optimize Amplifier's hook performance, clean up stale artifacts, fix broken references, and streamline agent/command catalog.

**Architecture:** Four independent stages, each producing a clean commit. Stage 1 (critical performance fix), Stage 2 (cleanup/archival), Stage 3 (hook consolidation), Stage 4 (command/agent rationalization).

**Tech Stack:** Bash, Python, YAML, Markdown

---

## Stage 1: Critical Performance Fix — Hook Guard (saves 30-90s/session)

### Task 1: Add bash guard to hook_post_tool_use.py wildcard hook

**Agent:** modular-builder

**Context:** `hook_post_tool_use.py` (line 12-15) checks `MEMORY_SYSTEM_ENABLED` env var and exits immediately if disabled (the default). But `uv run python` startup costs ~1.5s BEFORE the check runs. This fires on EVERY tool call (Read, Glob, Grep, Edit, Write, Bash...). With dozens of tool calls per session, this wastes 30-90s.

**Solution:** Wrap the `uv run` command in `.claude/settings.json` with a bash guard that checks the env var BEFORE launching Python.

**Files:**
- Modify: `.claude/settings.json` — PostToolUse wildcard hook (line 113-119)

- [ ] **Step 1: Replace the wildcard PostToolUse hook command**

Change from:
```json
{
  "matcher": "*",
  "hooks": [
    {
      "type": "command",
      "command": "cd C:/claude/amplifier && uv run .claude/tools/hook_post_tool_use.py"
    }
  ]
}
```

Change to:
```json
{
  "matcher": "*",
  "hooks": [
    {
      "type": "command",
      "command": "bash -c 'if [ \"${MEMORY_SYSTEM_ENABLED:-false}\" = \"true\" ]; then cd C:/claude/amplifier && uv run .claude/tools/hook_post_tool_use.py; fi'"
    }
  ]
}
```

- [ ] **Step 2: Verify hook still works when memory IS enabled**

Set env var and test:
```bash
MEMORY_SYSTEM_ENABLED=true bash -c 'if [ "${MEMORY_SYSTEM_ENABLED:-false}" = "true" ]; then echo "WOULD RUN"; fi'
```
Expected: "WOULD RUN"

- [ ] **Step 3: Verify hook skips when memory is disabled (default)**

```bash
bash -c 'if [ "${MEMORY_SYSTEM_ENABLED:-false}" = "true" ]; then echo "WOULD RUN"; else echo "SKIPPED"; fi'
```
Expected: "SKIPPED"

- [ ] **Step 4: Commit**
```bash
git add .claude/settings.json
git commit -m "perf: guard hook_post_tool_use.py with bash env check

Skip uv+Python startup (~1.5s) on every tool call when memory system
is disabled (the default). Saves 30-90s cumulative per session."
```

---

## Stage 2: Stale Artifact Cleanup & Broken Reference Fixes

### Task 2: Archive stale cowork documents

**Agent:** post-task-cleanup

**Context:** TODO.md, COWORK.md, HANDOFF.md, DISCOVERIES.md, DISCOVERIES-archive.md are remnants of the OpenCode/Gemini cowork experiment (Feb 2026). Most items are completed or stale. They consume attention on every session.

**Files:**
- Create: `docs/archive/` directory
- Move: `TODO.md` → `docs/archive/TODO.md`
- Move: `COWORK.md` → `docs/archive/COWORK.md`
- Move: `HANDOFF.md` → `docs/archive/HANDOFF.md`
- Move: `DISCOVERIES.md` → `docs/archive/DISCOVERIES.md`
- Move: `DISCOVERIES-archive.md` → `docs/archive/DISCOVERIES-archive.md`

- [ ] **Step 1: Create archive directory and move files**
```bash
mkdir -p docs/archive
git mv TODO.md docs/archive/
git mv COWORK.md docs/archive/
git mv HANDOFF.md docs/archive/
git mv DISCOVERIES.md docs/archive/
git mv DISCOVERIES-archive.md docs/archive/
```

- [ ] **Step 2: Verify no critical references break**
```bash
grep -rn "COWORK\.md\|HANDOFF\.md\|DISCOVERIES\.md\|TODO\.md" CLAUDE.md AGENTS.md .claude/commands/*.md
```
Expected: Only historical references in specs/plans (not load-bearing).

- [ ] **Step 3: Commit**
```bash
git add -A
git commit -m "chore: archive stale cowork artifacts to docs/archive/

Move TODO.md, COWORK.md, HANDOFF.md, DISCOVERIES.md, and
DISCOVERIES-archive.md. These are from the Feb 2026 OpenCode/Gemini
cowork experiment — most items completed or abandoned."
```

### Task 3: Fix AGENTS.md Makefile references

**Agent:** modular-builder

**Context:** AGENTS.md lines 176-189 reference `make install`, `make check`, `make test`, `make lock-upgrade` but no Makefile exists. Update to direct `uv run` equivalents.

**Files:**
- Modify: `AGENTS.md` — lines 176-189

- [ ] **Step 1: Replace Build/Test/Lint Commands section**

Find the section starting with `## Build/Test/Lint Commands` and replace:
```markdown
## Build/Test/Lint Commands

- Install dependencies: `uv sync`
- Add new dependencies: `uv add package-name` (in the specific project directory)
- Add development dependencies: `uv add --dev package-name`
- Run all checks: `uv run ruff check . && uv run ruff format --check .`
- Run all tests: `uv run pytest`
- Run a single test: `uv run pytest tests/path/to/test_file.py::TestClass::test_function -v`
- Upgrade dependency lock: `uv lock --upgrade`
```

- [ ] **Step 2: Commit**
```bash
git add AGENTS.md
git commit -m "fix: replace non-existent Makefile refs with uv commands in AGENTS.md"
```

### Task 4: Fix /visual command skill references

**Agent:** modular-builder

**Context:** `.claude/commands/visual.md` references `/generate-web-diagram`, `/generate-visual-plan`, etc. as slash commands. These are actually skills invoked via the Skill tool, not slash commands. The routing table should use skill names.

**Files:**
- Modify: `.claude/commands/visual.md` — lines 47-53, routing table

- [ ] **Step 1: Read the current visual.md**
Read the file fully to understand the routing structure.

- [ ] **Step 2: Update routing references**
Change all `/command-name` references to use the Skill tool pattern. Replace entries like:
```
/generate-web-diagram → Use Skill tool with skill="generate-web-diagram"
```
Ensure the routing table directs to `Skill(skill="generate-web-diagram")` etc. instead of slash command syntax.

- [ ] **Step 3: Commit**
```bash
git add .claude/commands/visual.md
git commit -m "fix: /visual routing — use Skill tool instead of slash command syntax"
```

### Task 5: Delete orphaned files and fix empty references

**Agent:** post-task-cleanup

**Files:**
- Delete: `ai_context/flow/FLOW_DRIVEN_DEVELOPMENT.md` (unreferenced)
- Delete: `ai_context/AMPLIFIER_CLAUDE_CODE_LEVERAGE.md` (unreferenced)
- Create: `ai_working/decisions/README.md` (referenced in AGENTS.md but empty directory)
- Delete: `.claude/commands/brainstorm-visual-companion.md` (references non-existent brainstorm-server/)

- [ ] **Step 1: Delete orphaned documentation**
```bash
git rm ai_context/flow/FLOW_DRIVEN_DEVELOPMENT.md
git rm ai_context/AMPLIFIER_CLAUDE_CODE_LEVERAGE.md
git rm .claude/commands/brainstorm-visual-companion.md
```

- [ ] **Step 2: Create decisions README**
Create `ai_working/decisions/README.md`:
```markdown
# Decision Records

Architectural decisions are documented here. Create a new record when making choices about:
- Architecture approaches
- Technology selection
- Pattern adoption or reversal

Format: `YYYY-MM-DD-<topic>.md` with sections: Context, Decision, Consequences.
```

- [ ] **Step 3: Verify no broken references**
```bash
grep -rn "FLOW_DRIVEN\|AMPLIFIER_CLAUDE_CODE_LEVERAGE\|brainstorm-visual-companion" CLAUDE.md AGENTS.md .claude/commands/*.md llms.txt
```
Expected: No matches in always-loaded files.

- [ ] **Step 4: Commit**
```bash
git add -A
git commit -m "chore: delete orphaned docs, create decisions README

Remove unreferenced ai_context files and brainstorm-visual-companion
(references non-existent brainstorm-server/). Seed ai_working/decisions/
README.md (referenced in AGENTS.md but was empty)."
```

---

## Stage 3: Hook Consolidation & Performance

### Task 6: Consolidate session-end-index.sh into single Python entry point

**Agent:** modular-builder

**Context:** `session-end-index.sh` (lines 16, 19, 22) runs 3 separate `uv run python` calls, each paying ~1.5s startup overhead. Consolidate into a single Python script that does all three tasks.

**Files:**
- Create: `scripts/recall/index-all.py`
- Modify: `.claude/hooks/session-end-index.sh`

- [ ] **Step 1: Create consolidated index script**

Create `scripts/recall/index-all.py`:
```python
#!/usr/bin/env python3
"""Consolidated recall indexer — runs all three indexing tasks in one process."""
import subprocess
import sys
from pathlib import Path

SCRIPTS_DIR = Path(__file__).parent

def run_script(name: str, args: list[str]) -> None:
    """Run a recall script, suppressing errors."""
    script = SCRIPTS_DIR / name
    if script.exists():
        try:
            subprocess.run([sys.executable, str(script)] + args,
                         capture_output=True, timeout=20)
        except (subprocess.TimeoutExpired, Exception):
            pass

def main() -> None:
    run_script("extract-sessions.py", ["--days", "3"])
    run_script("extract-docs.py", ["--recent", "3"])
    run_script("generate-doc-registry.py", [])

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Update session-end-index.sh**

Replace the 3 uv run python calls (lines 14-22) with a single call:
```bash
# Index sessions, docs, and regenerate registry in one Python process
uv run python scripts/recall/index-all.py 2>/dev/null
```

- [ ] **Step 3: Test the consolidated script**
```bash
cd C:/claude/amplifier && uv run python scripts/recall/index-all.py
```
Expected: Runs without error (may produce no output, that's fine).

- [ ] **Step 4: Commit**
```bash
git add scripts/recall/index-all.py .claude/hooks/session-end-index.sh
git commit -m "perf: consolidate session-end indexing into single Python process

Replace 3 separate uv run python calls (3x ~1.5s startup each) with
one process that runs all three indexing tasks. Saves ~3s on session end."
```

### Task 7: Add debounce to on_code_change_hook.sh

**Agent:** modular-builder

**Context:** `on_code_change_hook.sh` runs `make check` (lint+typecheck+format) on every Edit/Write. During rapid edits (5 files = 5x make check), this causes 15-50s overhead. Add a 30-second debounce.

**Files:**
- Modify: `.claude/tools/on_code_change_hook.sh` — add timestamp-based debounce at the top

- [ ] **Step 1: Add debounce logic at script start**

After the shebang and before any existing logic, add:
```bash
# Debounce: skip if make check ran within the last 30 seconds
DEBOUNCE_FILE="/tmp/amplifier-code-change-debounce"
if [[ -f "$DEBOUNCE_FILE" ]]; then
    LAST_RUN=$(cat "$DEBOUNCE_FILE" 2>/dev/null || echo 0)
    NOW=$(date +%s)
    ELAPSED=$(( NOW - LAST_RUN ))
    if [[ "$ELAPSED" -lt 30 ]]; then
        exit 0
    fi
fi
date +%s > "$DEBOUNCE_FILE"
```

- [ ] **Step 2: Test debounce**
```bash
# First run — should proceed
bash .claude/tools/on_code_change_hook.sh
# Second run within 30s — should skip
bash .claude/tools/on_code_change_hook.sh
```
Expected: Second run exits immediately.

- [ ] **Step 3: Commit**
```bash
git add .claude/tools/on_code_change_hook.sh
git commit -m "perf: add 30s debounce to on_code_change_hook.sh

Skip redundant make check runs during rapid edit sequences.
Prevents 5x lint+typecheck during multi-file edits."
```

---

## Stage 4: Command & Agent Rationalization

### Task 8: Deprecate /ultrathink-task

**Agent:** post-task-cleanup

**Context:** `/ultrathink-task` duplicates `/subagent-dev` — both orchestrate agents with review cycles. `/subagent-dev` is the canonical workflow (referenced by AGENTS.md, /brainstorm, /create-plan). `/ultrathink-task` is a looser version with no cross-references.

**Files:**
- Delete: `.claude/commands/ultrathink-task.md`

- [ ] **Step 1: Verify no critical references**
```bash
grep -rn "ultrathink" CLAUDE.md AGENTS.md .claude/commands/*.md
```
Expected: No load-bearing references.

- [ ] **Step 2: Delete the command**
```bash
git rm .claude/commands/ultrathink-task.md
```

- [ ] **Step 3: Commit**
```bash
git add -A
git commit -m "chore: remove /ultrathink-task (duplicates /subagent-dev)"
```

### Task 9: Fix routing-matrix agent role assignments

**Agent:** modular-builder

**Context:** Analysis found two agent role mismatches:
- `content-researcher`: scout/haiku but does research that needs reasoning → research/sonnet
- `bug-hunter`: research role but primarily implements fixes → implement/sonnet (agentic-search handles investigation)

**Files:**
- Modify: `config/routing-matrix.yaml`

- [ ] **Step 1: Update routing matrix**

In the agents section, change:
```yaml
  content-researcher: scout    # change to research
  bug-hunter: research         # change to implement
```

To:
```yaml
  content-researcher: research
  bug-hunter: implement
```

- [ ] **Step 2: Update AGENTS_CATALOG.md tier table**

Update the Model Tier Mapping table:
- `content-researcher` from Fast/haiku to Balanced/sonnet
- `bug-hunter` stays Balanced/sonnet (model doesn't change, just the role)

- [ ] **Step 3: Commit**
```bash
git add config/routing-matrix.yaml .claude/AGENTS_CATALOG.md
git commit -m "fix: correct content-researcher and bug-hunter role assignments

content-researcher: scout→research (needs reasoning, not just lookup)
bug-hunter: research→implement (fixes code, investigation uses agentic-search)"
```

### Task 10: Add frontmatter to commands missing it

**Agent:** modular-builder

**Files:**
- Modify: `.claude/commands/review-changes.md`
- Modify: `.claude/commands/prime.md`
- Modify: `.claude/commands/modular-build.md`

- [ ] **Step 1: Add frontmatter to review-changes.md**

Prepend:
```markdown
---
description: "Run build checks and tests on code changes. Quick validation: install deps, lint, format, type-check, test."
---

```

- [ ] **Step 2: Add frontmatter to prime.md**

Prepend:
```markdown
---
description: "Load project context: install dependencies, run checks and tests, prime the session for development."
---

```

- [ ] **Step 3: Add frontmatter to modular-build.md**

Prepend:
```markdown
---
description: "Build implementation from a specification using the modular-builder agent pattern. Self-contained module construction."
---

```

- [ ] **Step 4: Commit**
```bash
git add .claude/commands/review-changes.md .claude/commands/prime.md .claude/commands/modular-build.md
git commit -m "chore: add frontmatter to commands missing it

Standardize review-changes, prime, and modular-build commands
with description frontmatter for skill discovery."
```

---

## Verification

### Task 11: Final validation

**Agent:** post-task-cleanup

- [ ] **Step 1: Run health check**
```bash
bash scripts/validate-amplifier.sh
```
Expected: Fewer warnings than before (frontmatter added to 3 commands, orphaned files removed).

- [ ] **Step 2: Run routing matrix validation**
```bash
bash scripts/validate-routing-matrix.sh
```
Expected: 0 errors, fewer false-positive warnings.

- [ ] **Step 3: Verify no broken imports in CLAUDE.md**
```bash
grep "@" CLAUDE.md | head -5
```
Expected: @AGENTS.md and @config/routing-matrix.yaml both resolve.

- [ ] **Step 4: Verify stale files removed**
```bash
ls TODO.md COWORK.md HANDOFF.md 2>/dev/null
ls ai_context/flow/FLOW_DRIVEN_DEVELOPMENT.md 2>/dev/null
ls .claude/commands/execute-plan.md .claude/commands/ultrathink-task.md .claude/commands/brainstorm-visual-companion.md 2>/dev/null
```
Expected: All "No such file or directory"

- [ ] **Step 5: Final commit if any cleanup needed**
