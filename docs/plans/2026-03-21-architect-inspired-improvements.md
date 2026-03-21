# Architect-Inspired Improvements — Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add TaskDAG planning, plan caching with similarity matching, confidence scoring, cognitive journal, and expand the live dashboard with real-time data from all new data sources.

**Architecture:** Five features in priority order. Each is independently deployable. The dashboard expansion integrates data from all other features. All data flows through `${CLAUDE_PLUGIN_DATA}` JSONL files → FastAPI `/api/` endpoints → dashboard fetch().

**Tech Stack:** Python (scripts, FastAPI endpoints), JSONL (data), Bash (hooks), JavaScript (dashboard charts)

**Scope Mode:** HOLD SCOPE

---

## Data Flow

```
/create-plan                    /subagent-dev
    │                               │
    ▼                               ▼
TaskDAG JSON ──► plan-cache/ ──► journal.md
    │               │               │
    ▼               ▼               ▼
${CLAUDE_PLUGIN_DATA}/
├── plan-cache/
│   ├── index.json          ← plan hashes + similarity vectors
│   └── plans/              ← cached plan files
├── journal.md              ← cognitive journal (agent learnings)
├── reviews/history.jsonl   ← (existing)
├── failures.jsonl          ← (existing)
└── agent-stats.jsonl       ← NEW: per-agent dispatch outcomes
         │
         ▼
    FastAPI docs-server.py
    /api/metrics ← expanded with new data sources
    /api/plans   ← NEW: plan cache stats
    /api/journal ← NEW: recent journal entries
    /api/agents  ← NEW: agent performance leaderboard
         │
         ▼
    dashboard.html (fetch + auto-refresh)
```

---

## Stage A: TaskDAG in /create-plan

### Task A.1 [TRACER]: Add DAG output format to create-plan

**Agent:** modular-builder

**Files:**
- Modify: `commands/create-plan.md` (in plugin marketplace)

Currently `/create-plan` outputs flat markdown with manual wave analysis comments. Add a structured DAG section at the end of every plan:

- [ ] Read current `commands/create-plan.md`
- [ ] After the "Wave-Based Parallel Execution" section in the plan output template, add a `## TaskDAG` section:

```markdown
## TaskDAG

```json
{
  "tasks": [
    {"id": "1.1", "name": "Write sync script", "agent": "modular-builder", "depends_on": [], "confidence": 0.9, "parallel": true},
    {"id": "1.2", "name": "Run sync", "agent": "modular-builder", "depends_on": ["1.1"], "confidence": 0.95, "parallel": false}
  ],
  "critical_path": ["1.1", "1.2", "3.1"],
  "max_parallelism": 3,
  "total_tasks": 8,
  "estimated_minutes": 45
}
```

- [ ] Add instructions to `/create-plan` to generate this DAG alongside the markdown plan:
  - Each task gets: id, name, agent, depends_on (array of task IDs), confidence (0-1), parallel (bool)
  - Critical path: longest dependency chain
  - Max parallelism: largest set of tasks with no mutual dependencies
  - Confidence rules: research tasks → 0.7, implementation with spec → 0.9, greenfield → 0.6, config changes → 0.95

- [ ] Update `/subagent-dev` to read the DAG if present:
  - Parse `## TaskDAG` JSON block from plan
  - Use `depends_on` to auto-compute waves (replace manual wave analysis)
  - Use `confidence` to decide whether to dispatch `agentic-search` before implementation (confidence < 0.5)
  - Log parallelism stats: "DAG: 8 tasks, max parallelism 3, critical path length 4"

- [ ] Deploy to plugin marketplace
- [ ] Commit

```
feat: add TaskDAG output to /create-plan with dependency edges and confidence

Tasks now include depends_on, confidence scoring, and parallel flags.
/subagent-dev auto-computes waves from DAG instead of manual analysis.
```

---

## Stage B: Plan Caching with Similarity Matching

### Task B.1: Create plan cache infrastructure

**Agent:** modular-builder

**Files:**
- Create: `scripts/plan-cache.py`

Build a plan cache script that:

- [ ] **Store:** After `/create-plan` completes, hash the spec/prompt (SHA-256 of first 500 chars + file list), store plan file path + hash + timestamp + metadata in `${CLAUDE_PLUGIN_DATA}/plan-cache/index.json`
- [ ] **Lookup:** Given a new spec/prompt, compute hash, check index for exact match (instant) or similar match (compare sorted keyword lists, >70% overlap = match)
- [ ] **Evict:** Plans older than 30 days or with success_rate < 0.6 are auto-evicted
- [ ] **Success tracking:** After `/subagent-dev` completes, update the plan's success_rate in the index (pass = all tasks completed, partial = some failed, fail = blocked)

```python
# scripts/plan-cache.py
# Usage:
#   python plan-cache.py store --plan <path> --prompt "..."
#   python plan-cache.py lookup --prompt "..."
#   python plan-cache.py update --hash <hash> --outcome pass|partial|fail
#   python plan-cache.py evict
#   python plan-cache.py stats
```

- [ ] Index format:
```json
{
  "plans": [
    {
      "hash": "abc123",
      "prompt_keywords": ["exchange", "mailbox", "api"],
      "plan_path": "docs/plans/2026-03-20-exchange-api.md",
      "created": "2026-03-20T14:00:00Z",
      "success_rate": 0.85,
      "times_reused": 2,
      "task_count": 8
    }
  ]
}
```

- [ ] Commit

```
feat: add plan cache with similarity matching and success tracking
```

### Task B.2: Wire cache into /create-plan and /subagent-dev

**Agent:** modular-builder

**Files:**
- Modify: `commands/create-plan.md`
- Modify: `commands/subagent-dev.md` (in plugin marketplace)

- [ ] In `/create-plan`, before generating a new plan, run cache lookup:
```bash
AMPLIFIER_HOME="${AMPLIFIER_HOME:-$([ -d /opt/amplifier ] && echo /opt/amplifier || echo /c/claude/amplifier)}"
uv run python "$AMPLIFIER_HOME/scripts/plan-cache.py" lookup --prompt "$SPEC_SUMMARY"
```

- [ ] If match found (>70% similarity), ask user:
  - A) Adapt this plan (load and modify)
  - B) Generate fresh (ignore cache)
  - C) View cached plan first

- [ ] After plan is saved, store in cache:
```bash
uv run python "$AMPLIFIER_HOME/scripts/plan-cache.py" store --plan "$PLAN_PATH" --prompt "$SPEC_SUMMARY"
```

- [ ] In `/subagent-dev`, after all tasks complete, update cache:
```bash
uv run python "$AMPLIFIER_HOME/scripts/plan-cache.py" update --hash "$PLAN_HASH" --outcome "$OUTCOME"
```

- [ ] Deploy + commit

```
feat: wire plan cache into /create-plan and /subagent-dev pipeline
```

---

## Stage C: Cognitive Journal

### Task C.1: Add journal logging to /subagent-dev

**Agent:** modular-builder

**Files:**
- Modify: `commands/subagent-dev.md` (in plugin marketplace)

- [ ] After each task completes (regardless of outcome), append to `${CLAUDE_PLUGIN_DATA}/journal.md`:

```markdown
## 2026-03-21T14:30:00Z — Task 3: Implement mailbox API

**Agent:** modular-builder (sonnet) | **Status:** DONE | **Turns:** 18/25
**Plan:** docs/plans/2026-03-20-exchange-api.md
**Branch:** feat/exchange-api

**What happened:** Implemented 3 endpoints. First attempt missed the tenant isolation check — spec-reviewer caught it. Fixed on second dispatch.

**Learned:** Exchange API endpoints need PackageId scoping on every query. Add this as a default constraint in future exchange plans.
```

- [ ] The journal entry is written by the orchestrator (not the subagent) based on:
  - Agent name, model, status, turn count
  - Plan file reference
  - Whether review found issues (and what kind)
  - Any retries or model upgrades

- [ ] Keep journal to last 100 entries (rotate older entries to `journal-archive.md`)

- [ ] Commit

```
feat: add cognitive journal logging to /subagent-dev
```

### Task C.2: Add /api/journal endpoint to docs-server

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier-docs\docs-server.py`

- [ ] Add endpoint:
```python
@app.get("/api/journal")
async def get_journal(limit: int = 10):
    """Return recent journal entries."""
    journal_path = PLUGIN_DATA / "journal.md"
    if not journal_path.exists():
        return {"entries": [], "total": 0}
    content = journal_path.read_text(encoding="utf-8")
    # Parse ## entries, return last N
    entries = re.split(r'^## ', content, flags=re.MULTILINE)[1:]
    parsed = []
    for entry in entries[-limit:]:
        lines = entry.strip().split('\n')
        parsed.append({
            "header": lines[0] if lines else "",
            "content": '\n'.join(lines[1:]).strip()
        })
    return {"entries": list(reversed(parsed)), "total": len(entries)}
```

- [ ] Commit

```
feat: add /api/journal endpoint for cognitive journal entries
```

---

## Stage D: Agent Performance Tracking

### Task D.1: Add agent stats logging

**Agent:** modular-builder

**Files:**
- Modify: `commands/subagent-dev.md` (in plugin marketplace)

- [ ] After each agent dispatch (implementation + review), log to `${CLAUDE_PLUGIN_DATA}/agent-stats.jsonl`:

```json
{"timestamp":"2026-03-21T14:30:00Z","agent":"modular-builder","model":"sonnet","task":"Implement API","status":"DONE","turns_used":18,"turns_max":25,"review_pass":true,"retries":0,"plan":"exchange-api"}
```

- [ ] Commit

```
feat: add per-agent dispatch logging to agent-stats.jsonl
```

### Task D.2: Add /api/agents endpoint

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier-docs\docs-server.py`

- [ ] Add endpoint:
```python
@app.get("/api/agents")
async def get_agent_stats(days: int = 7):
    """Agent performance leaderboard."""
    entries = load_jsonl(PLUGIN_DATA / "agent-stats.jsonl", days)
    if not entries:
        return {"agents": [], "total_dispatches": 0}

    from collections import defaultdict
    stats = defaultdict(lambda: {"dispatches": 0, "success": 0, "retries": 0, "avg_turns": []})
    for e in entries:
        agent = e.get("agent", "unknown")
        stats[agent]["dispatches"] += 1
        if e.get("status") == "DONE":
            stats[agent]["success"] += 1
        stats[agent]["retries"] += e.get("retries", 0)
        stats[agent]["avg_turns"].append(e.get("turns_used", 0))

    leaderboard = []
    for agent, s in sorted(stats.items(), key=lambda x: -x[1]["dispatches"]):
        avg_t = sum(s["avg_turns"]) / len(s["avg_turns"]) if s["avg_turns"] else 0
        leaderboard.append({
            "agent": agent,
            "dispatches": s["dispatches"],
            "success_rate": round(s["success"] / s["dispatches"] * 100) if s["dispatches"] else 0,
            "total_retries": s["retries"],
            "avg_turns": round(avg_t, 1),
        })
    return {"agents": leaderboard, "total_dispatches": len(entries)}
```

- [ ] Commit

```
feat: add /api/agents endpoint for agent performance leaderboard
```

---

## Stage E: Dashboard Expansion

### Task E.1: Add new sections to dashboard

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier-docs\prompts\dashboard.md`
- Regenerate: `en/dashboard.html`, `pl/dashboard.html`

- [ ] Add these sections to the dashboard prompt (after existing sections):

**Section 5: Plan Cache** (after Session Velocity)
- Total cached plans, reuse count, average success rate
- Table: recent plans with hash, keywords, success rate, reuse count
- Data from: `fetch('/api/plans')` (new endpoint, see Task E.2)

**Section 6: Cognitive Journal** (after Plan Cache)
- Last 5 journal entries in collapsible cards
- Each card shows: timestamp, task, agent, status, what was learned
- Data from: `fetch('/api/journal')`

**Section 7: Agent Leaderboard** (after Cognitive Journal)
- Horizontal bar chart: dispatches by agent
- Table: agent name, dispatches, success rate, avg turns, retries
- Color-code: >90% success = green, 70-90% = yellow, <70% = red
- Data from: `fetch('/api/agents')`

- [ ] Update all fetch URLs to use the `apiBase` pattern (HTTPS port 8099)
- [ ] Add auto-refresh: dashboard polls `/api/metrics`, `/api/plans`, `/api/journal`, `/api/agents` every 60 seconds

- [ ] Commit prompt changes

```
feat: expand dashboard prompt with plan cache, journal, agent leaderboard
```

### Task E.2: Add /api/plans endpoint

**Agent:** modular-builder

**Files:**
- Modify: `C:\claude\amplifier-docs\docs-server.py`

- [ ] Add endpoint:
```python
@app.get("/api/plans")
async def get_plan_stats():
    """Plan cache statistics."""
    index_path = PLUGIN_DATA / "plan-cache" / "index.json"
    if not index_path.exists():
        return {"plans": [], "total": 0, "total_reuses": 0, "avg_success": 0}
    index = json.loads(index_path.read_text(encoding="utf-8"))
    plans = index.get("plans", [])
    total_reuses = sum(p.get("times_reused", 0) for p in plans)
    avg_success = sum(p.get("success_rate", 0) for p in plans) / len(plans) if plans else 0
    return {
        "plans": plans[-10:],
        "total": len(plans),
        "total_reuses": total_reuses,
        "avg_success": round(avg_success * 100),
    }
```

- [ ] Commit

```
feat: add /api/plans endpoint for plan cache stats
```

### Task E.3: Regenerate dashboard page

- [ ] Run: `cd C:\claude\amplifier-docs && uv run python generate.py --pages dashboard --force`
- [ ] Verify new sections appear in browser
- [ ] Commit generated HTML

```
docs: regenerate dashboard with plan cache, journal, agent leaderboard
```

---

## Wave Analysis

```
Wave 0 (solo):     Task A.1 [TRACER] — TaskDAG in create-plan
Wave 1 (parallel): Task B.1 + C.1 + D.1 (independent: cache script, journal, agent stats)
Wave 2 (parallel): Task B.2 + C.2 + D.2 + E.2 (wire into commands + API endpoints)
Wave 3 (solo):     Task E.1 — dashboard prompt expansion
Wave 4 (solo):     Task E.3 — regenerate dashboard HTML
```

## Verification Checklist

- [ ] `/create-plan` outputs TaskDAG JSON block with dependency edges
- [ ] `/subagent-dev` reads DAG and auto-computes waves
- [ ] `plan-cache.py store` creates index entry
- [ ] `plan-cache.py lookup` finds similar plans
- [ ] `${CLAUDE_PLUGIN_DATA}/journal.md` gets entries after /subagent-dev
- [ ] `${CLAUDE_PLUGIN_DATA}/agent-stats.jsonl` gets entries after agent dispatch
- [ ] `/api/plans` returns cache stats
- [ ] `/api/journal` returns recent entries
- [ ] `/api/agents` returns leaderboard
- [ ] Dashboard shows all new sections with live data
- [ ] Dashboard auto-refreshes every 60 seconds

## Task Count

| Stage | Tasks | Checkboxes |
|-------|-------|------------|
| A: TaskDAG | 1 | 6 |
| B: Plan Cache | 2 | 8 |
| C: Cognitive Journal | 2 | 5 |
| D: Agent Performance | 2 | 4 |
| E: Dashboard Expansion | 3 | 7 |
| **Total** | **10 tasks** | **30 checkboxes** |

## Estimated Effort

~2-3 hours in a fresh session. Stages A-D are all Python/markdown edits. Stage E requires one dashboard regeneration.
