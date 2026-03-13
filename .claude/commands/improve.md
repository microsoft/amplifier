---
description: "Iteratively improve agent output using AutoContext's improvement loop. Runs multiple rounds of evaluate-revise until threshold met."
---

# Improve — Iterative Output Refinement

## Overview

Takes agent output and iteratively refines it through AutoContext's improvement loop. Each round scores the output, identifies weaknesses, and produces an improved version. Stops when the threshold is met or max rounds exhausted.

**Announce at start:** "Improving: <task_name> (max <N> rounds, threshold <T>)."

## Arguments

$ARGUMENTS

## The Process

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- `task_name` — required (e.g., `code-review`, `implementation`)
- `--output "text"` — optional inline text
- `--file path` — optional file to read
- `--last` — use last agent response
- `--rounds N` — max improvement rounds (default: 3)
- `--threshold N` — target score to stop at (default: 80)

### Step 2: Ensure Task Exists

Same as `/evaluate` Step 2 — check task exists, create from template if needed.

```
Call: autocontext_get_agent_task(name=task_name)
```

If not found, follow the same template creation logic as `/evaluate`.

### Step 3: Get Initial Output

Same as `/evaluate` Step 3 — resolve from `--output`, `--file`, `--last`, or ask user.

### Step 4: Run Improvement Loop

```
Call: autocontext_run_improvement_loop(
  task_name=task_name,
  initial_output=<the output text>,
  max_rounds=<rounds>,
  threshold=<threshold>
)
```

### Step 5: Display Progress

Show a round-by-round progression table:

```
## Improvement: <task_name>

| Round | Score | Delta | Key Change |
|-------|-------|-------|------------|
| 0 (initial) | 62 | — | baseline |
| 1 | 71 | +9 | Added specificity to feedback |
| 2 | 78 | +7 | Covered security concerns |
| 3 | 84 | +6 | Improved tone and actionability |

**Result: 62 → 84 (+22 points in 3 rounds)**
```

### Step 6: Present Improved Output

Show the final improved version. If the output is long (>50 lines), write to a temp file and show the path instead.

### Step 7: Export Learnings (Optional)

If the improvement was significant (delta > 15 points):

```
Call: autocontext_export_agent_task_skill(task_name=task_name)
```

Report: "Learnings exported to AutoContext knowledge base. These will inform future evaluations."

### Step 8: Offer Next Steps

- If threshold met: "Target reached. Improved output ready."
- If threshold NOT met after max rounds: "Reached max rounds at score <N>. Options: run more rounds with `/improve <task> --rounds 5`, or adjust threshold."

## Integration Points

| After This Command... | Consider Running... |
|----------------------|---------------------|
| `/request-review` | `/improve code-review` on the review output |
| `modular-builder` finishes | `/evaluate implementation` → `/improve` if < 80 |
| `/brainstorm` design done | `/evaluate spec-writing` → `/improve` if needed |

## Common Mistakes

**Running too many rounds on diminishing returns**
- Fix: Default 3 rounds is usually enough. Diminishing returns after 5.

**Improving without evaluating first**
- Fix: `/improve` includes evaluation internally, but running `/evaluate` first gives you the baseline to compare.
