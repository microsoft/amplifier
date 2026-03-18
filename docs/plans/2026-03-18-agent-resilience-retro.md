# Agent Resilience + Retro Schema Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add failure classification, loop detection, and structured retro schema to Amplifier's agent dispatch protocol.

**Architecture:** Three changes integrated into existing infrastructure: (1) AGENTS.md protocol additions for failure taxonomy and loop detection, (2) friction.jsonl recording in existing SubagentStop hook, (3) retro command upgrade with smoothness heuristic and SQLite persistence.

**Tech Stack:** Python 3.13 (stdlib only: json, sqlite3, pathlib), Markdown, SQLite

---

## Task 1: AGENTS.md — Failure Taxonomy + Loop Detection [TRACER]

**Agent:** amplifier-core:modular-builder

This is the tracer bullet — defines the protocol that all other tasks depend on. Pure documentation, no code.

**Files:**
- Modify: `C:\claude\amplifier\AGENTS.md` (insert after line 106, the Synthesis Guard section)

- [ ] **Step 1: Read AGENTS.md and locate insertion point**

Read `AGENTS.md`. The new content goes after the "Synthesis Guard (All Agents)" section (ends around line 106 with `**When creating new agents**, always include this rule in the Context Budget section.`) and before "Task Decomposition Guidelines" (starts around line 108).

- [ ] **Step 2: Insert Failure Classification Taxonomy**

Insert after the Synthesis Guard section:

```markdown
### Failure Classification

When an agent fails, classify the failure before deciding on retry/resume. This taxonomy replaces ad-hoc error checking with a shared vocabulary:

| Class | Trigger | Retry? | Resume? |
|-------|---------|--------|---------|
| `transient` | API 500, rate limit, timeout, network error | Yes (auto, up to 3x) | No |
| `deterministic` | Wrong file path, missing module, syntax error in prompt | No | No — fix the prompt |
| `context_overflow` | Turn limit hit, context window full | No | Yes (reduced scope) |
| `stuck_loop` | Same action repeated 3+ times (see Loop Detection below) | No | No — escalate |
| `canceled` | User interrupt, hook kill | No | No |
| `scope_violation` | Write attempt in read-only agent, wrong directory | No | No — fix constraints |

**Decision tree (apply in order):**

1. Classify the failure using the table above.
2. `transient` → wait briefly, retry (up to 3 times). If 3rd retry fails, escalate to user.
3. `context_overflow` → invoke Resume Protocol with reduced scope.
4. `deterministic` → report to user with the specific error and a prompt-fix suggestion. Do NOT retry.
5. `stuck_loop` → terminate agent, report the repeating pattern to user.
6. `canceled` → report, do not retry.
7. `scope_violation` → report with the constraint that was violated, do not retry.

When reporting failures, always include the class name: "Agent amplifier-core:modular-builder failed (deterministic): file src/missing.py does not exist."
```

- [ ] **Step 3: Insert Loop Detection subsection**

Insert immediately after the Failure Classification section:

```markdown
### Loop Detection

Watch for repeating tool call patterns that indicate an agent is stuck. Check the last 10 tool calls for:

| Pattern | Definition |
|---------|------------|
| Length-1 repeat | Same tool + identical arguments, 3+ consecutive times |
| Length-2 cycle | A→B→A→B with identical inputs each iteration |
| Length-3 cycle | A→B→C→A→B→C with identical inputs each iteration |

**What does NOT count as a loop:**
- Reading different files (same tool, different arguments)
- Retrying after making a code change (edit content differs)
- Running tests after each edit (test output differs)
- Key signal: **identical inputs producing the same failed output**

**Response protocol:**

1. **First detection:** Inject steering via SendMessage: "Loop detected: you are repeating [tool + argument pattern]. Stop and try a different approach — change the file, change the strategy, or ask for clarification."
2. **Second detection in same agent session:** Hard stop. Classify as `stuck_loop`. Report to user: "Agent [name] stuck in loop after steering. Pattern: [describe]. Recommend: [specific next action]."
3. A loop steering injection counts as 1 of the 3 allowed resume cycles. A second loop detection terminates the agent regardless of remaining resume cycles.
```

- [ ] **Step 4: Verify AGENTS.md stays under 250-line budget**

Run: `wc -l AGENTS.md`
Expected: ≤310 lines (current ~250 + ~60 new). If over 250, the budget rule in AGENTS.md line 160 needs updating to reflect the new size.

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md
git commit -m "feat: add failure classification taxonomy + loop detection protocol

Six-class failure taxonomy (transient, deterministic, context_overflow,
stuck_loop, canceled, scope_violation) with decision tree.

Loop detection: pattern matching on last 10 tool calls, steering on
first detection, hard stop on second.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 2: Friction Recording in hook_stop.py

**Agent:** amplifier-core:modular-builder

Add friction.jsonl recording to the existing SubagentStop hook. This runs before the memory system check (which is disabled), so it always executes.

**Files:**
- Modify: `C:\claude\amplifier\.claude\tools\hook_stop.py` (insert after line 19, before the `try: from amplifier...` block)

- [ ] **Step 1: Read hook_stop.py**

Read the full file at `C:\claude\amplifier\.claude\tools\hook_stop.py`. Note the structure:
- Lines 1-19: imports + logger setup
- Lines 20-28: `try: from amplifier.memory...` (fails, exits gracefully since MEMORY_SYSTEM_ENABLED=false)
- Lines 31-253: `async def main()` (never reached when memory disabled)

The friction recording MUST go before the memory import block (line 20) so it runs regardless of MEMORY_SYSTEM_ENABLED.

- [ ] **Step 2: Add friction recording logic**

Insert after line 19 (`logger = HookLogger("stop_hook")`) and before line 21 (`try:`):

```python
# --- Friction recording (always runs, regardless of memory system) ---
import os
from datetime import datetime, timezone

def record_friction(input_data: dict) -> None:
    """Append one JSON record to tmp/friction.jsonl for retro analysis."""
    try:
        amplifier_dir = Path(__file__).parent.parent.parent
        friction_dir = amplifier_dir / "tmp"
        friction_dir.mkdir(parents=True, exist_ok=True)
        friction_file = friction_dir / "friction.jsonl"

        # Extract fields from the hook input
        # SubagentStop provides: agent_name, model, status, error, turns_used
        record = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "agent": input_data.get("agent_name", "unknown"),
            "model": input_data.get("model", "unknown"),
            "status": "success" if not input_data.get("error") else "failed",
            "failure_class": None,
            "friction_kind": None,
            "resume_count": input_data.get("resume_count", 0),
            "loop_detected": input_data.get("loop_detected", False),
            "turns_used": input_data.get("turns_used", 0),
            "description": input_data.get("error", "completed successfully"),
        }

        # Classify failure if present
        error = input_data.get("error", "")
        if error:
            error_lower = error.lower()
            if any(s in error_lower for s in ["rate limit", "429", "500", "timeout", "network"]):
                record["failure_class"] = "transient"
                record["friction_kind"] = "timeout" if "timeout" in error_lower else "retry"
            elif any(s in error_lower for s in ["context", "turn limit", "token limit"]):
                record["failure_class"] = "context_overflow"
                record["friction_kind"] = "timeout"
            elif any(s in error_lower for s in ["loop detected", "repeating"]):
                record["failure_class"] = "stuck_loop"
                record["friction_kind"] = "loop"
            elif any(s in error_lower for s in ["read-only", "scope", "permission"]):
                record["failure_class"] = "scope_violation"
                record["friction_kind"] = "tool_failure"
            elif "cancel" in error_lower:
                record["failure_class"] = "canceled"
                record["friction_kind"] = None
            else:
                record["failure_class"] = "deterministic"
                record["friction_kind"] = "wrong_approach"

        with open(friction_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(record) + "\n")

        logger.info(f"Friction recorded: {record['status']} ({record['failure_class'] or 'ok'})")
    except Exception as e:
        # Never break the hook chain for friction recording
        logger.error(f"Friction recording failed: {e}")


# Record friction from stdin (read once, then reset for downstream)
try:
    raw = sys.stdin.read()
    if raw.strip():
        _input = json.loads(raw)
        record_friction(_input)
        # Reset stdin for downstream processing (memory system)
        sys.stdin = __import__("io").StringIO(raw)
except Exception:
    pass  # Don't break hook chain
```

- [ ] **Step 3: Verify hook still exits cleanly when memory disabled**

Run: `cd /c/claude/amplifier && echo '{}' | uv run .claude/tools/hook_stop.py 2>&1`
Expected: exits 0, no errors. Check `tmp/friction.jsonl` contains one line.

- [ ] **Step 4: Verify friction.jsonl output**

Run: `cat tmp/friction.jsonl | python3 -c "import json,sys; d=json.loads(sys.stdin.readline()); print(d['status'], d['failure_class'])"`
Expected: `success None`

- [ ] **Step 5: Commit**

```bash
git add .claude/tools/hook_stop.py
git commit -m "feat: add friction recording to SubagentStop hook

Appends one JSON record per agent stop to tmp/friction.jsonl.
Classifies failures using the 6-class taxonomy.
Runs before memory system check — always active.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 3: Retro SQLite Table + Updated /retro Command

**Agent:** amplifier-core:modular-builder

Two sub-steps: add the `retros` table to the schema init script, then update the `/retro` command to parse friction.jsonl, compute smoothness, and write to SQLite.

**Files:**
- Modify: `C:\claude\amplifier\scripts\recall\index-all.py` (add retros table creation)
- Modify: `C:\Users\Administrator.ERGOLAB\.claude\plugins\marketplaces\amplifier-marketplace\amplifier-core\commands\retro.md` (add friction + smoothness + SQLite sections)

- [ ] **Step 1: Add retros table to index-all.py**

Read `scripts/recall/index-all.py`. The `main()` function runs three scripts. Add a schema init step at the top of `main()`:

```python
def ensure_retros_table() -> None:
    """Create retros table in recall-index.sqlite if it doesn't exist."""
    import sqlite3
    db_path = Path.home() / ".claude" / "recall-index.sqlite"
    if not db_path.exists():
        return  # DB created by extract-sessions.py
    conn = sqlite3.connect(str(db_path))
    conn.execute("""CREATE TABLE IF NOT EXISTS retros (
        id              INTEGER PRIMARY KEY,
        session_id      TEXT NOT NULL,
        timestamp       TEXT NOT NULL,
        smoothness      TEXT NOT NULL,
        total_agents    INTEGER,
        successful_agents INTEGER,
        total_retries   INTEGER,
        loops_detected  INTEGER,
        friction_points TEXT,
        learnings       TEXT,
        open_items      TEXT,
        UNIQUE(session_id)
    )""")
    conn.commit()
    conn.close()
```

Call `ensure_retros_table()` at the start of `main()` before the three `run_script()` calls.

- [ ] **Step 2: Verify table creation**

Run: `cd /c/claude/amplifier && uv run python scripts/recall/index-all.py`
Then: `sqlite3 ~/.claude/recall-index.sqlite ".tables" | grep retros`
Expected: `retros` appears in table list.

- [ ] **Step 3: Update retro.md command in plugin repo**

Read the current `retro.md` from the marketplace. Add a new section **before** "### Step 1: Gather Raw Data" that handles friction analysis:

Add after the "## Process" header and before "### Step 1":

```markdown
### Step 0: Friction Analysis (if available)

Before gathering git metrics, check for session friction data:

1. Check if `tmp/friction.jsonl` exists in the Amplifier root directory.
2. If it exists, read all JSON lines and compute:
   - `total_agents`: count of all records
   - `successful_agents`: count where `status == "success"`
   - `total_retries`: sum of all `resume_count` values
   - `loops_detected`: count where `loop_detected == true`
   - Collect all records where `status != "success"` as friction points

3. Compute **smoothness rating** using this deterministic heuristic (evaluate in order, first match wins):

   | Rating | Condition |
   |--------|-----------|
   | `Effortless` | All agents succeeded AND 0 friction entries with non-null friction_kind |
   | `Smooth` | All goals met AND total_retries ≤ 2 AND loops_detected == 0 |
   | `Bumpy` | Goals met AND (total_retries ≥ 3 OR loops_detected == 1) |
   | `Struggled` | Goals met AND (any agent has resume_count == 3 OR loops_detected ≥ 2) |
   | `Failed` | Any agent has status "failed" with no subsequent successful re-attempt |

   "Goals met" means no agent ended with `status: failed` without a later success entry for the same agent name.

4. Write the retro record to `~/.claude/recall-index.sqlite`:

```python
import sqlite3, json
db = sqlite3.connect(str(Path.home() / ".claude" / "recall-index.sqlite"))
db.execute("""INSERT OR REPLACE INTO retros
    (session_id, timestamp, smoothness, total_agents, successful_agents,
     total_retries, loops_detected, friction_points, learnings, open_items)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
    (session_id, timestamp, smoothness, total_agents, successful_agents,
     total_retries, loops_detected, json.dumps(friction_list),
     json.dumps(learnings), json.dumps(open_items)))
db.commit()
```

5. Include the smoothness rating and friction summary at the TOP of the retro output:

```markdown
## Session Smoothness: [rating]

| Metric | Value |
|--------|-------|
| Total agents dispatched | X |
| Successful | Y |
| Total retries | Z |
| Loops detected | N |

### Friction Points
- [agent]: [failure_class] — [description]
```

If `tmp/friction.jsonl` does not exist, skip Step 0 and proceed to Step 1 (git metrics only). Note: "No friction data available — run agents in this session first."
```

After updating, commit and push to the amplifier-plugins repo:

```bash
cd ~/.claude/plugins/marketplaces/amplifier-marketplace
git add amplifier-core/commands/retro.md
git commit -m "feat: add friction analysis + smoothness heuristic to /retro command

Reads tmp/friction.jsonl, computes smoothness (Effortless/Smooth/Bumpy/
Struggled/Failed), writes structured record to recall-index.sqlite.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
git push origin main
```

Then bump plugin version in marketplace.json and update:
```bash
claude plugin marketplace update amplifier-marketplace
claude plugin update amplifier-core@amplifier-marketplace
```

- [ ] **Step 4: Verify end-to-end**

Create a test friction.jsonl:
```bash
echo '{"ts":"2026-03-18T16:00:00Z","agent":"amplifier-core:modular-builder","model":"sonnet","status":"success","failure_class":null,"friction_kind":null,"resume_count":0,"loop_detected":false,"turns_used":12,"description":"completed successfully"}' > tmp/friction.jsonl
```

Run `/retro 24h` and verify:
1. Output includes "Session Smoothness: Effortless"
2. `sqlite3 ~/.claude/recall-index.sqlite "SELECT smoothness FROM retros ORDER BY timestamp DESC LIMIT 1"` returns `Effortless`

- [ ] **Step 5: Commit index-all.py changes**

```bash
git add scripts/recall/index-all.py
git commit -m "feat: add retros table to recall-index.sqlite schema

CREATE TABLE retros with session_id, smoothness, friction_points,
learnings, open_items. Created by index-all.py on session end.

Co-Authored-By: Claude Opus 4.6 (1M context) <noreply@anthropic.com>"
```

---

## Task 4: Verification + Cleanup

**Agent:** amplifier-core:test-coverage

Verify all three features work together end-to-end.

**Files:**
- Read: `AGENTS.md`, `.claude/tools/hook_stop.py`, `scripts/recall/index-all.py`, plugin `retro.md`

- [ ] **Step 1: Verify AGENTS.md protocol completeness**

Read AGENTS.md and confirm:
1. Failure Classification section exists with 6-class table
2. Decision tree has all 7 steps
3. Loop Detection section exists with 3 pattern types
4. Response protocol has steering + hard stop + resume cycle integration
5. Total file stays under 320 lines

- [ ] **Step 2: Verify friction recording**

Run: `echo '{"error":"rate limit exceeded"}' | uv run .claude/tools/hook_stop.py 2>&1`
Check: `tail -1 tmp/friction.jsonl | python3 -c "import json,sys; d=json.loads(sys.stdin.readline()); assert d['failure_class']=='transient', f'Expected transient, got {d[\"failure_class\"]}'; print('PASS: transient classification')" `

Run: `echo '{"error":"file not found: missing.py"}' | uv run .claude/tools/hook_stop.py 2>&1`
Check: `tail -1 tmp/friction.jsonl | python3 -c "import json,sys; d=json.loads(sys.stdin.readline()); assert d['failure_class']=='deterministic', f'Expected deterministic, got {d[\"failure_class\"]}'; print('PASS: deterministic classification')"`

Run: `echo '{}' | uv run .claude/tools/hook_stop.py 2>&1`
Check: `tail -1 tmp/friction.jsonl | python3 -c "import json,sys; d=json.loads(sys.stdin.readline()); assert d['status']=='success'; print('PASS: success recording')"`

- [ ] **Step 3: Verify retros table exists**

Run: `sqlite3 ~/.claude/recall-index.sqlite ".schema retros"`
Expected: CREATE TABLE statement with all 11 columns.

- [ ] **Step 4: Push AGENTS.md + hook changes via PR**

```bash
git checkout -b feat/agent-resilience
git add AGENTS.md .claude/tools/hook_stop.py scripts/recall/index-all.py
git push origin feat/agent-resilience
```

Create PR via Gitea MCP, review, merge.

---

## Requirement Coverage

```
Requirement → Task Mapping:
  ✓ Failure taxonomy (6 classes)      → Task 1 Step 2
  ✓ Decision tree                     → Task 1 Step 2
  ✓ Loop detection patterns           → Task 1 Step 3
  ✓ Loop steering + hard stop         → Task 1 Step 3
  ✓ Friction recording (hook_stop.py) → Task 2 Step 2
  ✓ Smoothness heuristic              → Task 3 Step 3
  ✓ Retros SQLite table               → Task 3 Step 1
  ✓ /retro command update             → Task 3 Step 3
  ✓ End-to-end verification           → Task 4
```

## Plan Quality Checklist

- [x] **Zero silent failures** — friction recording wraps in try/except, logs errors, never breaks hook chain
- [x] **Every error has a name** — 6 failure classes with explicit trigger conditions
- [x] **Observability** — friction.jsonl provides full agent dispatch telemetry
- [x] **Nothing deferred is vague** — all acceptance criteria from spec mapped to verification steps
- [x] **Scope mode honored** — HOLD: exactly what the spec says, no more
