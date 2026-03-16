---
description: "Evaluate Amplifier's own command outputs for continuous self-improvement. Scores brainstorm designs, plans, implementations against command-specific rubrics."
---

# Self-Eval — Amplifier Self-Improvement

## Overview

Meta-command that evaluates Amplifier's own command outputs. Scores them against command-specific rubrics and accumulates learnings in AutoContext's knowledge base. Over time, this builds a playbook of what makes each command's output better.

**Announce at start:** "Self-evaluating: <command_name>."

## Arguments

$ARGUMENTS

## Supported Commands & Rubrics

| Command | Task Name | Rubric Dimensions |
|---------|-----------|------------------|
| `brainstorm` | `amplifier-brainstorm` | Clarity, Completeness, YAGNI compliance, Agent allocation accuracy, Actionability |
| `create-plan` | `amplifier-create-plan` | Task granularity, Dependency ordering, Agent matching, Testability, Scope precision |
| `subagent-dev` | `amplifier-subagent-dev` | Spec compliance, Code quality, Test coverage, Zero-BS compliance, Completeness |
| `finish-branch` | `amplifier-finish-branch` | Cleanup thoroughness, PR quality, No leftover artifacts, Commit message quality |
| `debug` | `amplifier-debug` | Root cause accuracy, Hypothesis quality, Fix minimality, Evidence quality |

## The Process

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- `command_name` — one of: `brainstorm`, `create-plan`, `subagent-dev`, `finish-branch`, `debug`, or `all`
- `--output "text"` — optional inline text to evaluate
- `--last` — evaluate the last output from that command in this session

If `all` specified, evaluate all commands used in the current session.

### Step 2: Get Command Output

**If `--output` or `--last`:** use that text.

**If neither specified:** Search the current conversation for the most recent output from the specified command. Look for:
- `/brainstorm` → text between "Design Section" headers
- `/create-plan` → the plan output with task table
- `/subagent-dev` → the agent's implementation result
- `/finish-branch` → the PR creation summary
- `/debug` → the root cause analysis and fix

If no output found: "No recent <command_name> output found in this session. Provide output with --output or --last."

### Step 3: Ensure AutoContext Task Exists

Check if the amplifier-specific task exists:

```
Call: autocontext_get_agent_task(name=<task_name>)
```

**If not found, create it:**

```
Call: autocontext_create_agent_task(
  name=<task_name>,
  task_prompt=<command-specific prompt>,
  rubric=<command-specific rubric>
)
```

**Task definitions:**

**amplifier-brainstorm:**
- task_prompt: "Produce a design through collaborative brainstorming that is clear, complete, and ready for implementation."
- rubric: "Score 0-100 on: Clarity (unambiguous design sections), Completeness (covers architecture, data flow, error handling), YAGNI (no unnecessary features), Agent allocation (correct specialists assigned with clear responsibilities), Actionability (design can be handed to /create-plan without ambiguity)"

**amplifier-create-plan:**
- task_prompt: "Create an implementation plan with well-scoped tasks, correct agent assignments, and clear dependencies."
- rubric: "Score 0-100 on: Task granularity (each task is one clear deliverable), Dependency ordering (tasks flow logically), Agent matching (right specialist for each task), Testability (each task has verification criteria), Scope precision (no scope creep or missing requirements)"

**amplifier-subagent-dev:**
- task_prompt: "Implement a plan task with working code that meets the specification."
- rubric: "Score 0-100 on: Spec compliance (all requirements implemented), Code quality (clean, idiomatic, no dead code), Test coverage (tests written for new logic), Zero-BS compliance (no stubs, placeholders, or TODOs), Completeness (task fully done, not partial)"

**amplifier-finish-branch:**
- task_prompt: "Complete a development branch with thorough cleanup and a well-formed PR."
- rubric: "Score 0-100 on: Cleanup thoroughness (no debug artifacts, temp files), PR quality (clear title, description, test plan), No leftover artifacts (git status clean), Commit messages (conventional, descriptive)"

**amplifier-debug:**
- task_prompt: "Investigate and fix a bug with systematic root cause analysis."
- rubric: "Score 0-100 on: Root cause accuracy (found the real cause, not symptom), Hypothesis quality (systematic elimination), Fix minimality (smallest change that fixes the issue), Evidence quality (logs, tests, reproduction steps provided)"

### Step 4: Evaluate

```
Call: autocontext_evaluate_output(task_name=<task_name>, output=<command output>)
```

### Step 5: Present Results

```
## Self-Eval: /<command_name>

| Dimension | Score | Notes |
|-----------|-------|-------|
| <dim1>    | 85    | <feedback> |
| ...       | ...   | ...   |

**Overall: XX/100**

### What worked well
<strengths>

### What to improve next time
<specific, actionable suggestions>
```

### Step 6: Handle `all` Mode

If `command_name` is `all`:

1. Scan conversation for all command outputs used in this session
2. Run Steps 2-5 for each found command
3. Present a summary dashboard:

```
## Session Self-Eval

| Command | Score | Top Improvement |
|---------|-------|----------------|
| /brainstorm | 82 | Add data flow diagrams |
| /create-plan | 75 | Better task granularity |
| /subagent-dev | 88 | — |

**Session Average: 82/100**
```

### Step 7: Record Effort Metadata

After evaluation, record the effort context alongside the score. This feeds the adaptive effort steering loop.

```
Call: autocontext_record_feedback(
  task_name=<task_name>,
  feedback="{
    \"score\": <overall_score>,
    \"effort\": \"<resolved effort level: low/medium/high/max>\",
    \"turns_used\": <actual turns agent used>,
    \"turns_budget\": <max_turns that was set>,
    \"file_count\": <number of files in task>,
    \"agent_role\": \"<role from routing-matrix>\",
    \"model\": \"<model used>\",
    \"had_resume\": <true/false>,
    \"session_effort\": \"<current /effort setting>\"
  }"
)
```

### Step 7b: Write Recall-Indexable Summary + Outcome Record

Write a brief markdown summary so `/recall` can find self-eval results, AND append a structured outcome block that feeds the strategy learning flywheel:

```bash
mkdir -p .claude/skills/amplifier-self-improvement
cat > .claude/skills/amplifier-self-improvement/latest-eval.md << EVALEOF
# Self-Eval: /<command_name> — $(date +%Y-%m-%d)

**Score:** <overall_score>/100
**Effort:** <effort level> | **Turns:** <used>/<budget> | **Model:** <model>
**Dimensions:** <dim1>=<score>, <dim2>=<score>, ...

## Key Findings
<strengths and improvement suggestions — 2-3 bullets>

## Outcome: <domain-keyword>
- **Strategy:** agent=<agent>, model=<tier>, command=<command_name>
- **Domain:** <domain keyword, e.g., exchange-admin, api-design, frontend, bugfix>
- **Score:** <overall_score>/100
- **Retries:** <0-N, how many agent re-dispatches were needed>
- **Corrections:** <0-N, post-completion edits before user accepted>
- **Lesson:** <1 sentence — what worked or what should change next time>
EVALEOF
```

The `## Outcome:` block is the flywheel record. `/recall Outcome: <domain>` retrieves it in future sessions, allowing `/brainstorm` and `/create-plan` to learn from past strategies. Each session that runs `/self-eval` makes future sessions smarter.

This file gets indexed by the recall doc indexer (category: `skill`), making self-eval results searchable via `/recall self-eval` or `/recall brainstorm score`.

### Step 8: Accumulate Learnings

Check if score patterns exist:

```
Call: autocontext_get_best_output(task_name=<task_name>)
```

If this evaluation improves on previous best, note it. If score is consistently low on a dimension across evaluations, flag it:

> "Pattern detected: /brainstorm consistently scores low on Agent Allocation (avg 68). Consider reviewing agent catalog before finalizing designs."

**Effort patterns to surface:**
- "Implementation tasks with 3+ files score 20% higher at high effort vs medium"
- "Review tasks show no quality difference between medium and high — save the budget"
- "Scout tasks above low effort waste turns with no score improvement"

## The Flywheel

```
Command runs → /self-eval scores it (with effort metadata)
    → AutoContext accumulates learnings
    → playbook identifies optimal effort per task type
    → effort resolver reads playbook → better effort selection next time
```

**Future:** Observer hook auto-runs `/self-eval` on SessionEnd.

## Common Mistakes

**Evaluating partial outputs**
- Fix: Wait until the command finishes before evaluating

**Running self-eval too frequently on the same command**
- Fix: Once per session per command is enough. Patterns emerge over multiple sessions.
