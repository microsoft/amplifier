---
description: "Execute implementation plans with review checkpoints. Loads a plan, reviews it critically, then executes tasks in batches."
---

# Executing Plans

## Branch Gate (REQUIRED)

Before doing ANY work, check the current branch and refuse to proceed if on main or master:

```bash
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "ERROR: Cannot run /execute-plan on branch '$CURRENT_BRANCH'."
  echo "Create a feature branch first:"
  echo "  Option 1: /worktree  (recommended — isolated environment)"
  echo "  Option 2: git checkout -b feature/<name>"
  exit 1
fi
```

**If on main/master:** STOP. Do not execute any plan steps. Tell the user to create a feature branch first, then re-run this command.

**If on a feature branch:** Proceed.

## Process Graph (Authoritative)

> When this graph conflicts with prose, follow the graph.

```dot
digraph execute_plan {
  rankdir=TB;

  "branch_gate" [label="Branch Gate\ncheck current branch" shape=diamond];
  "on_main" [label="STOP: on main/master\nCreate feature branch first" shape=box style=filled fillcolor=red fontcolor=white];
  "load_plan" [label="Load plan from docs/plans/" shape=box];
  "review_plan" [label="Review plan\n(all tasks and context)" shape=box];
  "batch_tasks" [label="Group tasks into batches\n(3-5 tasks per batch)" shape=box];
  "execute_batch" [label="Execute current batch\n(task by task)" shape=box];
  "checkpoint" [label="Checkpoint: batch complete\nreport to user" shape=box];
  "user_review" [label="User approves batch?" shape=diamond];
  "revise" [label="Revise based on feedback" shape=box];
  "more_batches" [label="More batches remain?" shape=diamond];
  "done" [label="/finish-branch" shape=box style=filled fillcolor=lightgreen];

  "branch_gate" -> "on_main" [label="main/master"];
  "branch_gate" -> "load_plan" [label="feature branch"];
  "load_plan" -> "review_plan";
  "review_plan" -> "batch_tasks";
  "batch_tasks" -> "execute_batch";
  "execute_batch" -> "checkpoint";
  "checkpoint" -> "user_review";
  "user_review" -> "revise" [label="needs changes"];
  "revise" -> "execute_batch";
  "user_review" -> "more_batches" [label="approved"];
  "more_batches" -> "execute_batch" [label="yes"];
  "more_batches" -> "done" [label="no"];
}
```

## Overview

Load plan, review critically, execute tasks in batches, report for review between batches.

**Core principle:** Batch execution with checkpoints for architect review.

**Announce at start:** "I'm using the executing-plans skill to implement this plan."

## The Process

### Step 1: Load and Review Plan
1. Read plan file
2. Review critically - identify any questions or concerns about the plan
3. If concerns: Raise them with your human partner before starting
4. If no concerns: Create TodoWrite and proceed

**Session Naming:** After loading the plan, rename this session:

/rename exec: <plan-name>

Derive the name from the plan filename. Example: `/rename exec: email-forwarding`

If `/rename` is unavailable, skip this step.

### Step 2: Execute Batch
**Default: First 3 tasks**

For each task:
1. Mark as in_progress
2. Follow each step exactly (plan has bite-sized steps)
3. Run verifications as specified
4. Mark as completed

### Step 3: Report
When batch complete:
- Show what was implemented
- Show verification output
- Say: "Ready for feedback."

### Step 4: Continue
Based on feedback:
- Apply changes if needed
- Execute next batch
- Repeat until complete

### Step 5: Complete Development

After all tasks complete and verified:
- Announce: "I'm using /finish-branch to complete this work."
- **REQUIRED:** Use `/finish-branch`
- Follow that skill to verify tests, present options, execute choice

## When to Stop and Ask for Help

**STOP executing immediately when:**
- Hit a blocker mid-batch (missing dependency, test fails, instruction unclear)
- Plan has critical gaps preventing starting
- You don't understand an instruction
- Verification fails repeatedly

**Ask for clarification rather than guessing.**

## When to Revisit Earlier Steps

**Return to Review (Step 1) when:**
- Partner updates the plan based on your feedback
- Fundamental approach needs rethinking

**Don't force through blockers** - stop and ask.

## Remember
- Review plan critically first
- Follow plan steps exactly
- Don't skip verifications
- Reference skills when plan says to
- Between batches: just report and wait
- Stop when blocked, don't guess
- Never start implementation on main/master branch without explicit user consent

## Integration

**Required workflow skills:**
- `/worktree` - REQUIRED: Set up isolated workspace before starting
- `/create-plan` - Creates the plan this command executes
- `/finish-branch` - Complete development after all tasks
- `/verify` - Verification before completion
