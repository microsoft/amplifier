---
description: "Development retrospective — analyze commit history, work patterns, velocity, and code quality metrics. Supports time windows: 24h, 7d, 14d, 30d."
effort: low
---
# /retro — Development Retrospective

Analyze recent development activity: commits, velocity, churn hotspots, and quality signals. Produces a structured report with actionable observations.

**Announce at start:** "Running retro for [window]."

## Arguments

$ARGUMENTS

Parse for:
- **Time window**: `24h`, `7d` (default), `14d`, `30d`, or custom like `3d`
- **Compare mode**: `vs-previous` — compare window against the same-length prior period
- **Focus**: optional keyword filter (e.g., `retro 7d auth` scopes to auth-related work)

Examples: `/retro` | `/retro 24h` | `/retro 14d vs-previous` | `/retro 30d exchange`

## Process

### Step 0: Friction Analysis (if available)

Before gathering git metrics, check for session friction data:

1. Check if `tmp/friction.jsonl` exists in the Amplifier root directory (`C:\claude\amplifier` on Windows, `/opt/amplifier` on Linux).
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
   from pathlib import Path
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

   - `session_id`: derive from the session's JSONL filename or use the current date+time
   - `learnings`: populated from the Step 2 analysis (categories: `repo`, `code`, `workflow`, `tool`)
   - `open_items`: populated from Step 2 recommendations (kinds: `tech_debt`, `follow_up`, `investigation`, `test_gap`)

5. Include the smoothness rating and friction summary at the **TOP** of the retro output, before the git metrics:

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

If `tmp/friction.jsonl` does not exist, skip Step 0 and proceed to Step 1 (git metrics only). Note in the output: "No friction data available for this session."

### Step 1: Gather Raw Data

Dispatch a haiku scout subagent (read-only, 12 turns) to collect git metrics:

```
Task(subagent_type="general-purpose", model="haiku", max_turns=12, description="Gather retro metrics for [window]", prompt="
  **READ-ONLY MODE: Use ONLY Bash for read-only git commands (git log, git shortlog, git diff --stat; NO git checkout, git reset, git push, or file-modifying commands), Glob, and Grep. Do NOT modify any files.**

  When nearing your turn limit, STOP tool calls and produce your summary with whatever data you have collected. Partial metrics are more valuable than no output. Reserve at least 2 turns for writing your response.

  Run these git commands (adjust --since to the parsed window):

  # Commit log
  git log --oneline --since='[window]' --no-merges

  # Dated commit log for velocity calculation
  git log --format='%h %ad %s' --date=short --since='[window]' --no-merges
  # Most-changed files (top 30)
  git log --since='[window]' --no-merges --format='' --name-only | sort | uniq -c | sort -rn | head -30
  # Authors
  git shortlog -sn --since='[window]' --no-merges
  # Churn hotspots (modified files only, top 20)
  git log --since='[window]' --no-merges --format='' --diff-filter=M --name-only | sort | uniq -c | sort -rn | head -20
  # Lines added/removed summary
  git log --since='[window]' --no-merges --stat --format=''
  # TODO/FIXME introduced
  git log --since='[window]' --no-merges -p | grep -c '^\+.*TODO\|FIXME\|HACK\|XXX' || echo '0'
  # Merge/PR activity
  git log --since='[window]' --merges --oneline
  # New files created
  git log --since='[window]' --no-merges --diff-filter=A --format='' --name-only | wc -l
  # Files deleted
  git log --since='[window]' --no-merges --diff-filter=D --format='' --name-only | wc -l

  Return a structured summary (MAX 600 words) with: commit count, lines +/-, top 10 changed files, author breakdown, churn hotspots, TODO count, merge count, new/deleted file counts.
")

If **vs-previous** mode: run the same commands for the prior period (e.g., 7d window → `--since="14 days ago" --until="7 days ago"`).

If **focus** keyword: append `-- "*[keyword]*"` path filter to git log commands.

### Step 2: Analyze Patterns

From the raw data, compute:

1. **Velocity** — commits/day average, lines added vs removed, net codebase growth, PRs merged
2. **Work distribution** — classify commits by message prefix/content into: features, bug fixes, refactoring, docs/config, chores
3. **Churn hotspots** — files changed 3+ times in the window; flag potential instability
4. **Quality signals**:
   - TODO/FIXME count (tech debt accumulation)
   - Fix commits following feature commits in same window (quality gaps)
   - Revert commits (plan failures)
5. **Focus areas** — which directories/modules got the most attention

If **vs-previous**: calculate deltas for velocity, focus shift, and quality trends.

### Step 3: Present Report

Output a structured report:

```markdown
# Retro: [start] to [end] ([window])

## Velocity
- **Commits**: X (Y/day avg) [arrow vs previous if comparing]
- **Lines**: +A / -B (net +C)
- **Files touched**: N unique files
- **PRs merged**: M

## Work Distribution
| Category | Commits | % |
|----------|---------|---|
| Features | X | Y% |
| Bug fixes | X | Y% |
| Refactoring | X | Y% |
| Docs/config | X | Y% |

## Focus Areas
| Directory/Module | Changes | Top Files |
|-----------------|---------|-----------|
| src/module/ | N | file1, file2 |

## Churn Hotspots (3+ changes)
| File | Changes | Nature |
|------|---------|--------|
| path/to/file | N | feature/fix/churn |

## Quality Signals
- **New TODOs/FIXMEs**: +X
- **Fix-after-feature**: X instances
- **Reverts**: X

## Amplifier Metrics

Run the review report script to get aggregated stats for the time window:

```bash
AMPLIFIER_HOME="${AMPLIFIER_HOME:-$([ -d /opt/amplifier ] && echo /opt/amplifier || echo /c/claude/amplifier)}"
uv run python "$AMPLIFIER_HOME/scripts/review-report.py" --days WINDOW_DAYS 2>/dev/null
```

Replace `WINDOW_DAYS` with the retro window (1 for 24h, 7 for 7d, 14 for 14d, 30 for 30d).

If the script returns data, include it in the report:

```
AMPLIFIER METRICS (last N days)
═══════════════════════════════
Reviews:    N total | N PASS | N FAIL (X% pass rate)
  By engine: sonnet: N | codex: N | gemini: N
  Findings:  N P1 | N P2 | N P3
Failures:   N rate_limit | N auth | N network
```

If the script returns no data or fails, skip this section silently.

## Key Observations
- [3-5 bullets: what went well, what's concerning, what to watch]

## Recommendations
- [2-3 actionable suggestions based on the data]
```

If **vs-previous** mode, add a **Comparison** section before Key Observations showing deltas.

### Step 4: Save Snapshot (optional)

Ask the user if they want to persist the retro. If yes:
- Save to `ai_working/retros/YYYY-MM-DD-retro.md` in the current repo
- When previous retros exist, note trends across retros in the Observations section

## When to Use

- Weekly standup preparation
- After a development surge (many commits in short time)
- Before sprint planning (understand recent velocity)
- After incidents (what was changing when things broke?)
- Monthly codebase health check
