---
description: "Development retrospective — analyze commit history, work patterns, velocity, and code quality metrics. Supports time windows: 24h, 7d, 14d, 30d."
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

### Step 1: Gather Raw Data

Dispatch a **haiku scout subagent** (read-only, 12 turns) to collect git metrics from the current repo.

**READ-ONLY MODE: Use ONLY Bash (git commands), Glob, Grep. Do NOT modify any files.**

Run these git commands (adjust `--since` to the parsed window):

```bash
# Commit log
git log --oneline --since="[window]" --no-merges

# Dated commit log for velocity calculation
git log --format="%h %ad %s" --date=short --since="[window]" --no-merges

# Most-changed files (top 30)
git log --since="[window]" --no-merges --format="" --name-only | sort | uniq -c | sort -rn | head -30

# Authors
git shortlog -sn --since="[window]" --no-merges

# Churn hotspots (modified files only, top 20)
git log --since="[window]" --no-merges --format="" --diff-filter=M --name-only | sort | uniq -c | sort -rn | head -20

# Lines added/removed summary
git log --since="[window]" --no-merges --stat --format=""

# TODO/FIXME introduced
git log --since="[window]" --no-merges -p | grep -c "^\+.*\(TODO\|FIXME\|HACK\|XXX\)" || echo "0"

# Merge/PR activity
git log --since="[window]" --merges --oneline

# New files created
git log --since="[window]" --no-merges --diff-filter=A --format="" --name-only | wc -l

# Files deleted
git log --since="[window]" --no-merges --diff-filter=D --format="" --name-only | wc -l
```

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
