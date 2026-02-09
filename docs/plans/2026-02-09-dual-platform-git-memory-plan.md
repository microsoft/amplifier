# Dual-Platform Git Memory Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development to execute this plan task-by-task. Each task specifies its Agent -- dispatch that Amplifier agent as the subagent for implementation.

**Goal:** Integrate the Gemini-developed git-notes memory system into Claude Code's superpowers installation, enabling cross-platform memory sharing via git push/pull.

**Architecture:** Pull fork changes to local superpowers, add SessionStart hook for auto-sync, wire memory CLI tools into amplifier agent protocol. Git notes as shared transport layer.

**Tech Stack:** Node.js (git-notes tools), Python (Claude Code hooks), Git, Bash

---

### Task 1: Sync local superpowers with fork

**Agent:** integration-specialist

**Files:**
- Modify: `C:\claude\superpowers\` (git pull)

**Step 1: Pull latest fork changes**

Run:
```bash
cd /c/claude/superpowers && git pull origin main
```
Expected: All Gemini-developed commits (git-notes-state, memory-ops, commands/) pulled to local.

**Step 2: Verify core files exist**

Run:
```bash
ls /c/claude/superpowers/lib/git-notes-state.js /c/claude/superpowers/lib/state-schema.js /c/claude/superpowers/lib/memory-ops.js /c/claude/superpowers/commands/recall.js /c/claude/superpowers/commands/memorize.js /c/claude/superpowers/commands/snapshot-memory.js
```
Expected: All files present (exit 0).

**Step 3: Verify Node.js can run the tools**

Run:
```bash
cd /c/claude/superpowers && node commands/recall.js knowledge_base 2>&1 || echo "OK - no notes yet"
```
Expected: Either JSON output or "not found" (git notes may not exist yet).

**Step 4: Initialize git notes if needed**

Run:
```bash
cd /c/claude/superpowers && git notes --ref refs/notes/superpowers show 2>/dev/null || echo '{"metadata":{"last_agent":"init","timestamp":"'$(date -Iseconds)'"}}' | git notes --ref refs/notes/superpowers add -f -m "$(cat)"
```
Expected: Git notes ref initialized with empty state.

**Step 5: Commit any local changes if needed**

Only if local files were modified. Otherwise skip.

---

### Task 2: Add git-notes sync to Claude Code SessionStart hook

**Agent:** integration-specialist

**Files:**
- Modify: `C:\claude\amplifier\.claude\settings.json` (add hook if not present)
- Create: `C:\claude\amplifier\.claude\tools\hook_memory_sync.py` (new hook script)

**Context:** Claude Code runs hooks on SessionStart. We need a hook that:
1. Fetches git notes from origin
2. Reads the current memory state
3. Outputs a brief summary for context injection

**Step 1: Create the memory sync hook script**

Create `C:\claude\amplifier\.claude\tools\hook_memory_sync.py`:

```python
#!/usr/bin/env python3
"""SessionStart hook: Sync git-notes memory from origin."""
import subprocess
import json
import sys
import os

SUPERPOWERS_DIR = os.path.expanduser("~/.claude/plugins/cache/superpowers-marketplace/superpowers")
# Fallback to local superpowers
if not os.path.isdir(SUPERPOWERS_DIR):
    SUPERPOWERS_DIR = "C:/claude/superpowers"

NOTES_REF = "refs/notes/superpowers"


def run(cmd, cwd=None, check=False):
    """Run a command and return stdout."""
    try:
        result = subprocess.run(
            cmd, capture_output=True, text=True, cwd=cwd, check=check, timeout=15
        )
        return result.stdout.strip()
    except (subprocess.CalledProcessError, subprocess.TimeoutExpired, FileNotFoundError):
        return ""


def main():
    # Try to fetch notes from origin (non-blocking, 10s timeout)
    run(["git", "fetch", "origin", f"{NOTES_REF}:{NOTES_REF}"], cwd=SUPERPOWERS_DIR)

    # Read current state
    state_json = run(["git", "notes", "--ref", NOTES_REF, "show"], cwd=SUPERPOWERS_DIR)

    if not state_json:
        print("Git memory: No notes found (fresh state)")
        return

    try:
        state = json.loads(state_json)
    except json.JSONDecodeError:
        print("Git memory: Notes exist but invalid JSON")
        return

    # Summary output
    kb = state.get("knowledge_base", {})
    decisions = kb.get("decisions", [])
    patterns = kb.get("patterns", [])
    glossary = kb.get("glossary", {})

    parts = []
    if decisions:
        parts.append(f"{len(decisions)} decisions")
    if patterns:
        parts.append(f"{len(patterns)} patterns")
    if glossary:
        parts.append(f"{len(glossary)} glossary terms")

    last_agent = state.get("metadata", {}).get("last_agent", "unknown")

    if parts:
        print(f"Git memory synced: {', '.join(parts)} (last: {last_agent})")
    else:
        print(f"Git memory synced: empty state (last: {last_agent})")


if __name__ == "__main__":
    main()
```

**Step 2: Register hook in settings.json**

Add to the hooks array in `.claude/settings.json` under `hooks.SessionStart`:
```json
{
  "type": "command",
  "command": "python .claude/tools/hook_memory_sync.py"
}
```

**Step 3: Verify hook runs**

Run manually:
```bash
cd /c/claude/amplifier && python .claude/tools/hook_memory_sync.py
```
Expected: "Git memory synced: ..." or "No notes found"

**Step 4: Commit**

```bash
cd /c/claude/amplifier
git add .claude/tools/hook_memory_sync.py
git commit -m "feat: add git-notes memory sync on SessionStart"
```

---

### Task 3: Add memory push to PreCompact hook

**Agent:** integration-specialist

**Files:**
- Modify: `C:\claude\amplifier\.claude\tools\hook_precompact.py`

**Context:** Before context compaction, push any git notes changes to origin so the other machine can pick them up.

**Step 1: Read current hook_precompact.py**

Check existing content and add git notes push logic.

**Step 2: Add notes push to existing PreCompact hook**

Append to the existing `hook_precompact.py`:

```python
def push_memory_notes():
    """Push git notes to origin before compaction."""
    import subprocess
    superpowers_dir = os.path.expanduser("~/.claude/plugins/cache/superpowers-marketplace/superpowers")
    if not os.path.isdir(superpowers_dir):
        superpowers_dir = "C:/claude/superpowers"

    try:
        subprocess.run(
            ["git", "push", "origin", "refs/notes/superpowers"],
            cwd=superpowers_dir,
            capture_output=True,
            timeout=15
        )
    except Exception:
        pass  # Non-critical - don't block compaction
```

Call `push_memory_notes()` from the main function.

**Step 3: Verify**

Run:
```bash
cd /c/claude/amplifier && python .claude/tools/hook_precompact.py
```
Expected: No errors.

**Step 4: Commit**

```bash
git add .claude/tools/hook_precompact.py
git commit -m "feat: push git-notes memory on PreCompact"
```

---

### Task 4: Create memory convenience wrapper for Claude Code

**Agent:** modular-builder

**Files:**
- Create: `C:\claude\amplifier\.claude\tools\memory.py`

**Context:** Claude Code agents need a simple way to recall/memorize without knowing Node.js paths. Create a Python wrapper that calls the Node.js tools.

**Step 1: Create memory.py wrapper**

```python
#!/usr/bin/env python3
"""Memory convenience wrapper for Claude Code agents."""
import subprocess
import sys
import os
import json

SUPERPOWERS_DIR = os.path.expanduser("~/.claude/plugins/cache/superpowers-marketplace/superpowers")
if not os.path.isdir(SUPERPOWERS_DIR):
    SUPERPOWERS_DIR = "C:/claude/superpowers"


def recall(path):
    """Query memory at given dot-path."""
    result = subprocess.run(
        ["node", os.path.join(SUPERPOWERS_DIR, "commands", "recall.js"), path],
        capture_output=True, text=True, cwd=SUPERPOWERS_DIR
    )
    return result.stdout.strip()


def memorize(section, value):
    """Store a value in memory at given section."""
    if isinstance(value, (dict, list)):
        value = json.dumps(value)
    result = subprocess.run(
        ["node", os.path.join(SUPERPOWERS_DIR, "commands", "memorize.js"),
         "--section", section, "--value", value],
        capture_output=True, text=True, cwd=SUPERPOWERS_DIR
    )
    return result.stdout.strip()


def snapshot():
    """Generate human-readable memory snapshot."""
    result = subprocess.run(
        ["node", os.path.join(SUPERPOWERS_DIR, "commands", "snapshot-memory.js")],
        capture_output=True, text=True, cwd=SUPERPOWERS_DIR
    )
    return result.stdout.strip()


if __name__ == "__main__":
    action = sys.argv[1] if len(sys.argv) > 1 else "help"
    if action == "recall" and len(sys.argv) > 2:
        print(recall(sys.argv[2]))
    elif action == "memorize" and len(sys.argv) > 3:
        print(memorize(sys.argv[2], sys.argv[3]))
    elif action == "snapshot":
        print(snapshot())
    else:
        print("Usage: memory.py recall <path> | memorize <section> <value> | snapshot")
```

**Step 2: Verify**

Run:
```bash
cd /c/claude/amplifier && python .claude/tools/memory.py recall knowledge_base
```
Expected: JSON output or empty.

**Step 3: Commit**

```bash
git add .claude/tools/memory.py
git commit -m "feat: add memory convenience wrapper for Claude Code agents"
```

---

### Task 5: Test cross-platform memory flow

**Agent:** test-coverage

**Step 1: Store a test decision via Claude Code**

Run:
```bash
cd /c/claude/superpowers && node commands/memorize.js --section knowledge_base.decisions --value '{"id":"ADR-001","title":"Use git notes for cross-platform memory","status":"accepted","context":"Need shared state between Claude Code and Gemini/OpenCode on different machines","decision":"Use git notes ref refs/notes/superpowers as transport layer"}'
```

**Step 2: Verify recall works**

Run:
```bash
cd /c/claude/superpowers && node commands/recall.js knowledge_base.decisions
```
Expected: Array with ADR-001.

**Step 3: Verify snapshot generates**

Run:
```bash
cd /c/claude/superpowers && node commands/snapshot-memory.js
```
Expected: `docs/memory/SNAPSHOT.md` created with ADR-001 content.

**Step 4: Verify git notes push**

Run:
```bash
cd /c/claude/superpowers && git push origin refs/notes/superpowers
```
Expected: Notes pushed to origin.

**Step 5: Verify Python wrapper**

Run:
```bash
cd /c/claude/amplifier && python .claude/tools/memory.py recall knowledge_base.decisions
```
Expected: Same ADR-001 output.

**Step 6: Run SessionStart hook**

Run:
```bash
cd /c/claude/amplifier && python .claude/tools/hook_memory_sync.py
```
Expected: "Git memory synced: 1 decisions"

---

### Task 6: Push all changes

**Agent:** post-task-cleanup

**Step 1: Push amplifier changes**

```bash
cd /c/claude/amplifier && git push origin main
```

**Step 2: Verify superpowers is up to date**

```bash
cd /c/claude/superpowers && git status
```

**Step 3: Generate final memory snapshot**

```bash
cd /c/claude/superpowers && node commands/snapshot-memory.js
```
