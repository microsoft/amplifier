---
description: "Score agent output against a quality rubric using AutoContext. Supports pre-built templates (code-review, implementation, spec-writing) or custom tasks."
---

# Evaluate — Score Agent Output

## Overview

Score any agent output against a structured rubric. Returns per-dimension scores (0-100) and an overall rating. Uses AutoContext's evaluation engine via MCP.

**Announce at start:** "Evaluating: <task_name>."

## Arguments

$ARGUMENTS

## Pre-Built Task Templates

These templates auto-create in AutoContext on first use:

| Template | Rubric Dimensions |
|----------|------------------|
| `code-review` | Thoroughness, Actionability, Specificity, Tone, Coverage |
| `implementation` | Correctness, Style consistency, Completeness, Error handling, Readability |
| `spec-writing` | Clarity, Completeness, Testability, Scope precision, Agent allocation |

## The Process

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- `task_name` — required (e.g., `code-review`, `implementation`, or custom name)
- `--output "text"` — optional inline text to evaluate
- `--file path` — optional file to read as output
- `--last` — use the last agent response from this session

If no output source specified, ask the user what to evaluate.

### Step 2: Ensure Task Exists

Check if the agent task exists in AutoContext:

```
Call: autocontext_get_agent_task(name=task_name)
```

**If task exists:** proceed to Step 3.

**If task doesn't exist and matches a template** (`code-review`, `implementation`, `spec-writing`):

Create it using the template rubric:

```
Call: autocontext_create_agent_task(
  name=task_name,
  task_prompt=<template prompt>,
  rubric=<template rubric>
)
```

**Template definitions:**

**code-review:**
- task_prompt: "Produce a thorough code review that identifies issues, suggests improvements, and provides actionable feedback."
- rubric: "Score 0-100 on: Thoroughness (covers all changed code), Actionability (suggestions are specific and implementable), Specificity (references exact lines/patterns), Tone (professional, constructive), Coverage (logic, security, performance, style all addressed)"

**implementation:**
- task_prompt: "Implement the specified feature or fix with clean, working code that follows project conventions."
- rubric: "Score 0-100 on: Correctness (code works as specified), Style (follows project conventions), Completeness (all requirements met), Error handling (edge cases covered), Readability (clear naming, minimal complexity)"

**spec-writing:**
- task_prompt: "Write a design specification that is clear, complete, and actionable for implementation."
- rubric: "Score 0-100 on: Clarity (unambiguous language), Completeness (all requirements captured), Testability (acceptance criteria are verifiable), Scope (no YAGNI violations), Agent allocation (correct specialists assigned)"

**If task doesn't exist and no template matches:** Ask the user to provide a task prompt and rubric, then create it.

### Step 3: Get Output to Evaluate

Based on the source flag:
- `--output "text"` → use directly
- `--file path` → read the file
- `--last` → extract last agent response from conversation context
- No flag → ask user to paste or specify

### Step 4: Evaluate

```
Call: autocontext_evaluate_output(task_name=task_name, output=<the output text>)
```

### Step 5: Present Results

Display a structured report:

```
## Evaluation: <task_name>

| Dimension | Score | Notes |
|-----------|-------|-------|
| <dim1>    | 85    | <feedback> |
| <dim2>    | 72    | <feedback> |
| ...       | ...   | ...   |

**Overall: XX/100**

<summary of strengths and weaknesses>
```

### Step 6: Offer Next Steps

If overall score < 80:
> Score below 80. Run `/improve <task_name>` to iteratively refine this output?

If overall score >= 80:
> Solid output. Learnings saved to AutoContext knowledge base.

## Common Mistakes

**Evaluating without a rubric**
- Fix: Always ensure task exists with rubric before evaluating

**Using wrong template for the output type**
- Fix: Match template to what's being evaluated (code → implementation, review → code-review)

## Red Flags

- Never evaluate empty output — check length first
- Never create duplicate tasks — check existence before creating
