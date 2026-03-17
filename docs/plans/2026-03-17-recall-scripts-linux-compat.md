# Recall Scripts Linux Compatibility Fix

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Fix 4 bugs in recall scripts that cause incorrect behavior on Linux: hardcoded Windows path encodings, dead code in extract-docs, and silent error swallowing in index-all.

**Architecture:** The recall scripts under `scripts/recall/` resolve Claude Code project directories using hardcoded `C--claude-amplifier` (Windows path encoding). On Linux, the encoding is `-opt-amplifier`. Fix by detecting the correct project directory dynamically. Also remove dead CATEGORY_PATTERNS and add stderr logging to index-all.

**Tech Stack:** Python 3.12+, pathlib, sqlite3

---

## File Map

| File | Action | Responsibility |
|------|--------|---------------|
| `scripts/recall/recall-search.py` | Modify L26 | Fix MEMORY_DIR to find correct project dir |
| `scripts/recall/recall_day.py` | Modify L130-133 | Fix get_project_dirs() to check both encodings |
| `scripts/recall/extract-docs.py` | Modify L77-80 | Remove dead CATEGORY_PATTERNS for `.claude/` dirs |
| `scripts/recall/index-all.py` | Modify L21-22 | Add stderr logging instead of silent pass |

---

## Error Map

| Codepath | What Can Fail | Handling |
|----------|--------------|----------|
| recall-search.py MEMORY_DIR | Dir doesn't exist | Already handled: search returns empty results gracefully |
| recall_day.py get_project_dirs | Neither dir exists | Already handled: falls back to scanning all dirs |
| index-all.py run_script | Script crashes | Currently silent — fix: print to stderr |

---

### Task 1: Fix MEMORY_DIR in recall-search.py [TRACER]

**Agent:** bug-hunter

**Files:**
- Modify: `scripts/recall/recall-search.py:26`

- [ ] **Step 1: Verify the bug**

Run: `python3 -c "from pathlib import Path; p = Path.home() / '.claude/projects/C--claude-amplifier/memory'; print(f'exists={p.exists()}, files={list(p.iterdir()) if p.exists() else []}')"` and compare with `-opt-amplifier/memory`.

Expected: `-opt-amplifier/memory` has files, `C--claude-amplifier/memory` is empty or missing.

- [ ] **Step 2: Fix MEMORY_DIR resolution**

Replace `recall-search.py` line 26:

```python
# OLD:
MEMORY_DIR = Path.home() / ".claude" / "projects" / "C--claude-amplifier" / "memory"

# NEW — try both Linux and Windows encodings:
def _find_memory_dir() -> Path:
    """Find amplifier memory directory (platform-agnostic)."""
    base = Path.home() / ".claude" / "projects"
    for name in ("-opt-amplifier", "C--claude-amplifier"):
        candidate = base / name / "memory"
        if candidate.is_dir():
            return candidate
    return base / "-opt-amplifier" / "memory"  # default to Linux

MEMORY_DIR = _find_memory_dir()
```

- [ ] **Step 3: Verify the fix**

Run: `uv run python scripts/recall/recall-search.py "test" -n 1` — should return results from the correct memory directory.

- [ ] **Step 4: Commit**

```bash
git add scripts/recall/recall-search.py
git commit -m "fix: resolve MEMORY_DIR for Linux path encoding"
```

---

### Task 2: Fix get_project_dirs() in recall_day.py

**Agent:** bug-hunter

**Files:**
- Modify: `scripts/recall/recall_day.py:126-133`

- [ ] **Step 1: Fix get_project_dirs to check both encodings**

Replace lines 126-133:

```python
# OLD:
def get_project_dirs(all_projects: bool) -> list[Path]:
    """Get project directories to scan."""
    if all_projects:
        return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]
    amplifier = CLAUDE_PROJECTS / "C--claude-amplifier"
    if amplifier.exists():
        return [amplifier]
    return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]

# NEW:
def get_project_dirs(all_projects: bool) -> list[Path]:
    """Get project directories to scan."""
    if all_projects:
        return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]
    for name in ("-opt-amplifier", "C--claude-amplifier"):
        candidate = CLAUDE_PROJECTS / name
        if candidate.exists():
            return [candidate]
    return [d for d in CLAUDE_PROJECTS.iterdir() if d.is_dir()]
```

- [ ] **Step 2: Verify the fix**

Run: `uv run python scripts/recall/recall_day.py list --days 1` — should find sessions from the Linux project directory.

- [ ] **Step 3: Commit**

```bash
git add scripts/recall/recall_day.py
git commit -m "fix: check Linux path encoding first in get_project_dirs"
```

---

### Task 3: Remove dead CATEGORY_PATTERNS in extract-docs.py

**Agent:** bug-hunter

**Files:**
- Modify: `scripts/recall/extract-docs.py:77-80`

- [ ] **Step 1: Understand why they're dead**

`should_skip_dir()` at line 109-111 skips all directories starting with `.`, which means `.claude/agents/`, `.claude/commands/`, `.claude/skills/`, `.claude/context/` are never reached during `os.walk`. The patterns at lines 77-80 can never match.

- [ ] **Step 2: Remove dead patterns**

Delete lines 77-80 (the four `.claude/` patterns). Keep line 81 (`ai_context/`) and everything else — those CAN match since `ai_context` doesn't start with `.`.

After removal, the patterns section should flow:
```python
    (re.compile(r"^docs/reviews/"), "review"),
    (re.compile(r"^docs/reports/"), "report"),
    (re.compile(r"^ai_context/"), "philosophy"),
    (re.compile(r"^context/"), "context"),
```

- [ ] **Step 3: Verify**

Run: `uv run python scripts/recall/extract-docs.py --recent 0` — should complete without errors.

- [ ] **Step 4: Commit**

```bash
git add scripts/recall/extract-docs.py
git commit -m "fix: remove dead CATEGORY_PATTERNS for dot-prefixed dirs"
```

---

### Task 4: Add error logging to index-all.py

**Agent:** bug-hunter

**Files:**
- Modify: `scripts/recall/index-all.py:11-22`

- [ ] **Step 1: Replace silent error swallowing with stderr logging**

```python
# OLD:
def run_script(name: str, args: list[str]) -> None:
    """Run a recall script, suppressing errors."""
    script = SCRIPTS_DIR / name
    if script.exists():
        try:
            subprocess.run(
                [sys.executable, str(script)] + args,
                capture_output=True,
                timeout=20,
            )
        except (subprocess.TimeoutExpired, Exception):
            pass

# NEW:
def run_script(name: str, args: list[str]) -> None:
    """Run a recall script, logging errors to stderr."""
    script = SCRIPTS_DIR / name
    if not script.exists():
        return
    try:
        result = subprocess.run(
            [sys.executable, str(script)] + args,
            capture_output=True,
            timeout=20,
        )
        if result.returncode != 0:
            print(f"[index-all] {name} failed (exit {result.returncode})", file=sys.stderr)
            if result.stderr:
                print(f"  {result.stderr.decode(errors='replace')[:200]}", file=sys.stderr)
    except subprocess.TimeoutExpired:
        print(f"[index-all] {name} timed out after 20s", file=sys.stderr)
    except Exception as e:
        print(f"[index-all] {name} error: {e}", file=sys.stderr)
```

- [ ] **Step 2: Verify**

Run: `uv run python scripts/recall/index-all.py` — should complete cleanly. If any sub-script fails, error should appear on stderr.

- [ ] **Step 3: Commit**

```bash
git add scripts/recall/index-all.py
git commit -m "fix: log errors instead of silently swallowing in index-all"
```

---

### Task 5: Run all shell tests and verify

**Agent:** post-task-cleanup

- [ ] **Step 1: Run lint and format checks**

```bash
uv run ruff check scripts/recall/ && uv run ruff format --check scripts/recall/
```

- [ ] **Step 2: Run shell tests**

```bash
bash tests/hooks/test_session_end_index.sh
```

- [ ] **Step 3: Run modified scripts end-to-end**

```bash
uv run python scripts/recall/recall-search.py "test" -n 1
uv run python scripts/recall/recall_day.py list --days 1
uv run python scripts/recall/extract-docs.py --recent 0
uv run python scripts/recall/index-all.py
```

All should succeed without errors.
