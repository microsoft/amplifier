---
description: "Propose evidence-based CLAUDE.md updates from AutoContext learnings and self-eval scores."
---

# Self-Improve — Evidence-Based Instruction Updates

## Overview

Reads accumulated evidence from AutoContext evaluations, observer logs, and session history, then proposes concrete edits to CLAUDE.md, AGENTS.md, and routing-matrix.yaml. Every proposed change cites its evidence source. Nothing is auto-applied — the user reviews and approves each change.

**Announce at start:** "Running self-improvement cycle. Gathering evidence..."

## Arguments

$ARGUMENTS

Optional: `--apply` to auto-apply non-controversial changes (still shows diff before committing).

## The Process

### Step 1: Gather Evidence from All Sources

Run these in parallel to collect improvement signals:

**1a. AutoContext feedback and playbook:**
```
Call: autocontext_get_best_output(task_name="amplifier-brainstorm")
Call: autocontext_get_best_output(task_name="amplifier-subagent-dev")
Call: autocontext_get_best_output(task_name="amplifier-create-plan")
Call: autocontext_get_best_output(task_name="amplifier-finish-branch")
Call: autocontext_get_best_output(task_name="amplifier-debug")
Call: autocontext_get_best_output(task_name="bug-fix")
```

For each task that returns data, note the score, effort level, and any dimension consistently scoring low.

**1b. AutoContext skill discoveries:**
```
Call: autocontext_skill_discover(query="amplifier workflow improvement")
Call: autocontext_search_strategies(query="optimal effort configuration")
```

**1c. Observer logs:**
```bash
cat /tmp/amplifier-observations.jsonl 2>/dev/null | tail -20
cat /tmp/amplifier-observations.prev.jsonl 2>/dev/null | tail -20
```

Look for patterns: recurring build failures, stale branch warnings, etc.

**1d. Recent self-eval summaries:**
```bash
cat .claude/skills/amplifier-self-improvement/latest-eval.md 2>/dev/null
```

**1e. Session recall — recent patterns:**
Search for recent improvement-relevant conversations:
```bash
cd "$AMPLIFIER_HOME" && uv run python scripts/recall/recall-search.py "improvement optimization" -n 5 2>/dev/null
```

### Step 2: Analyze Evidence and Identify Improvements

For each evidence source, classify findings into improvement categories:

| Category | Target File | Example |
|----------|------------|---------|
| Turn budget adjustment | `config/routing-matrix.yaml` | "implement role agents consistently need resume cycles → increase max turns" |
| Effort tier correction | `config/routing-matrix.yaml` | "scout agents score same at low vs medium effort → keep low" |
| Model tier adjustment | `config/routing-matrix.yaml` | "code-quality-reviewer returns BLOCKED on haiku → bump to sonnet" |
| Operating principle update | `CLAUDE.md` | "brainstorm scores higher with data flow diagrams → add to guidance" |
| Agent protocol refinement | `AGENTS.md` | "subagents frequently miss synthesis → strengthen guard language" |
| Command cross-reference | `.claude/commands/*.md` | "users often run /evaluate after /subagent-dev → add suggestion" |

**Filter rules:**
- Only propose changes backed by 2+ data points (not one-off observations)
- Never propose changes that contradict user feedback memories
- Never modify FuseCP-specific content (that's project knowledge, not platform guidance)
- Prefer small, targeted edits over broad rewrites

### Step 3: Generate Improvement Proposals

For each identified improvement, produce a structured proposal:

```markdown
## Proposal N: <title>

**Evidence:**
- Source 1: <what was observed, with data>
- Source 2: <confirming observation>

**Current state:**
<quote the current text in the target file>

**Proposed change:**
<show the exact edit — old → new>

**Impact:** <what improves and why>

**Risk:** Low / Medium / High
- Low: documentation/comment update, no behavioral change
- Medium: turn budget or effort adjustment, may affect dispatch behavior
- High: operating principle change, affects all sessions
```

### Step 4: Present Proposals to User

Group proposals by risk level (Low first, then Medium, then High):

```
## Self-Improvement Proposals — <N> changes from <M> evidence sources

### Low Risk (documentation/config)
[proposals...]

### Medium Risk (behavioral adjustments)
[proposals...]

### High Risk (principle changes)
[proposals...]

Apply all Low+Medium? (High risk requires individual approval)
```

### Step 5: Apply Approved Changes

For each approved proposal:

1. Read the target file
2. Apply the exact edit specified in the proposal
3. Verify the edit was applied correctly

After all edits:

```bash
git add CLAUDE.md AGENTS.md config/routing-matrix.yaml .claude/commands/*.md
git commit -m "chore: self-improvement cycle — <N> evidence-based updates

<list each change with its evidence summary, one per line>

Co-Authored-By: Claude Opus 4.6 <noreply@anthropic.com>"
```

### Step 6: Record the Cycle

Write a summary of what was changed and why:

```bash
mkdir -p .claude/skills/amplifier-self-improvement
cat > .claude/skills/amplifier-self-improvement/last-cycle.md << EOF
# Self-Improvement Cycle — $(date +%Y-%m-%d)

## Changes Applied
<list of changes with evidence>

## Changes Deferred
<proposals that were rejected or need more data>

## Data Quality
- AutoContext tasks with data: <N>/<total>
- Observer entries analyzed: <N>
- Self-eval summaries found: <N>
EOF
```

This file is indexed by recall for future reference.

## What It Never Does

- **Never auto-applies changes** without `--apply` flag, and even then shows diff first
- **Never modifies user memory files** — those are the user's preferences, not platform config
- **Never changes FuseCP-specific content** — project knowledge stays separate from platform guidance
- **Never proposes changes from a single data point** — requires 2+ observations
- **Never contradicts user feedback** — feedback memories override all other evidence

## When to Run

- After 5+ sessions of active use (enough data to find patterns)
- After a batch of `/self-eval` runs (fresh evaluation data)
- When you notice recurring issues (same agent BLOCKED, same review findings)
- Periodically: once per week is enough

## Integration

**Feeds from:**
- `/self-eval` → scores and effort metadata
- `/evaluate` → output quality scores
- AutoContext → accumulated playbooks and strategies
- Observers → build failures, drift patterns
- `/recall` → session history patterns

**Updates:**
- `CLAUDE.md` — operating principles, context strategy
- `AGENTS.md` — turn budgets, protocols, decomposition guidelines
- `config/routing-matrix.yaml` — model tiers, effort levels, turn ranges
- `.claude/commands/*.md` — cross-references, dispatch parameters
