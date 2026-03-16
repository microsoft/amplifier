---
description: "Build reusable strategy for recurring problems via AutoContext multi-agent loop."
---

# Solve — Evolve Reusable Strategies

## Overview

When you keep hitting the same problem, `/solve` uses AutoContext's full multi-agent evolution loop (Competitor → Analyst → Coach → Architect → Curator) to build a reusable strategy. The result is a portable skill package that gets imported into your knowledge base.

This is the heavyweight tool — it can take minutes. Use `/evaluate` and `/improve` for quick tasks.

**Announce at start:** "Solving: <description> (generations: <N>)."

## Arguments

$ARGUMENTS

## The Process

### Step 1: Parse Arguments

Extract from `$ARGUMENTS`:
- `--description "problem description"` or the full argument text as description
- `--gens N` — number of evolution generations (default: 3)

If no description provided, ask: "What recurring problem should I build a strategy for?"

### Step 2: Start Solve Job

```
Call: autocontext_solve_scenario(
  description=<problem description>,
  generations=<gens>
)
```

This returns a `job_id`.

Report: "Solve job started (ID: <job_id>). This runs AutoContext's full evolution loop — may take several minutes."

### Step 3: Poll for Completion

Loop with increasing intervals:

```
Call: autocontext_solve_status(job_id=<job_id>)
```

Check status field:
- `running` → wait, report progress if generation count changed
- `completed` → proceed to Step 4
- `failed` → report error, suggest retry with fewer generations

**Progress reporting:** Each time the generation count advances, report:
```
Generation <N>/<total>: <current best score>
```

**Timeout:** If no progress after 10 minutes, report and ask user if they want to continue waiting.

### Step 4: Get Result

```
Call: autocontext_solve_result(job_id=<job_id>)
```

### Step 5: Import Skill Package

```
Call: autocontext_import_package(<result package>)
```

This lands the skill in `.claude/skills/`.

### Step 6: Present Results

```
## Solved: <description>

**Skill:** <skill_name>
**Best Score:** <score>/100
**Generations:** <N>
**Exported to:** .claude/skills/<skill_name>/

### Strategy Summary
<playbook excerpt — key insights>

### Operational Lessons
<top 3-5 lessons learned>

This strategy is now available via `/recall` and will be discovered
automatically when relevant problems arise.
```

### Step 7: Notify

If ntfy.sh is configured:
```bash
bash scripts/notify.sh "Solve Complete" "<skill_name> scored <score>/100" 3
```

## Example Usage

```
/solve Debug IIS application pool crashes on Windows Server
/solve Exchange PowerShell remoting failures across different auth methods
/solve Optimizing SQL queries that hit parameter sniffing issues
/solve --description "Blazor component rendering issues with large datasets" --gens 5
```

## Common Mistakes

**Using /solve for one-off problems**
- Fix: `/solve` is for recurring problems worth investing in. Use `/debug` for one-offs.

**Too few generations for complex problems**
- Fix: Start with 3, increase to 5-7 if the problem is multi-dimensional.

## Red Flags

- Never run `/solve` on trivially simple problems — it's expensive
- Always check `/recall` first — the strategy may already exist
