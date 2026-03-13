# AutoContext Integration — Evaluate, Improve, Solve, Self-Eval

**Date:** 2026-03-13
**Status:** Validated Design
**Branch:** feature/tier3-routing-observers-foreman

---

## Problem

Amplifier has no way to score agent outputs against quality rubrics, iteratively improve them, or accumulate reusable strategies for recurring problems. Knowledge from past sessions exists in `/recall` but there's no structured evaluation or self-improvement loop.

## Goal

Integrate autocontext (https://github.com/greyhaven-ai/autocontext) as an MCP server and wrap its key workflows in four practical Amplifier commands. Bridge autocontext's knowledge system with `/recall` for unified knowledge access.

## Non-Goals

- Sandbox/multi-user isolation (not our use case)
- Tournament/match/game-specific tools
- MLX distillation (future)
- OpenClaw artifact publishing
- Monitor tools (we have observers)

---

## Phase 1: MCP Server Setup

Add autocontext to `.mcp.json`:

```json
"autocontext": {
  "command": "cmd",
  "args": ["/c", "cd", "C:\\claude\\autocontext\\autocontext", "&&", "uv", "run", "autoctx", "mcp-serve"],
  "env": {
    "AUTOCONTEXT_AGENT_PROVIDER": "anthropic"
  }
}
```

**Prerequisite:** `cd C:\claude\autocontext\autocontext && uv sync`

No extra API key — inherits `ANTHROPIC_API_KEY` from environment.

---

## Phase 2: `/evaluate` Command

The daily workhorse. Score any agent output against a rubric.

### Flow

1. Parse arguments: `task_name` (required), optional `--output` inline text
2. If no task exists, create one: ask user for task prompt + rubric (or use pre-built template)
3. Call `autocontext_evaluate_output(task_name, output)`
4. Display score breakdown (0-100 per dimension + overall)
5. If score < threshold, offer: "Run `/improve` to iterate?"

### Pre-built task templates (shipped with command)

- `code-review` — thoroughness, actionability, tone
- `implementation` — correctness, style, completeness
- `spec-writing` — clarity, completeness, testability

Templates auto-create the agent task in autocontext on first use.

### Example

```
/evaluate code-review --output "$(cat /tmp/last-review.md)"
```

---

## Phase 3: `/improve` Command

Iteratively refine agent output using autocontext's improvement loop.

### Flow

1. Parse arguments: `task_name` (required), `--rounds N` (default 3), `--threshold N` (default 80)
2. Get initial output: `--output` inline, or read from last agent result
3. Call `autocontext_run_improvement_loop(task_name, initial_output, max_rounds=N, threshold=N)`
4. Display each round's score progression as a table
5. Return best version with before/after score comparison
6. Optionally export learnings: `autocontext_export_agent_task_skill(task_name)`

### Integration with existing workflow

- After `/request-review` → `/improve` the review
- After `modular-builder` produces code → `/evaluate implementation` → `/improve` if score < 80
- After `/brainstorm` produces a spec → `/evaluate spec-writing` → `/improve` if needed

### Example

```
/improve code-review --rounds 5 --threshold 85
```

---

## Phase 4: `/solve` Command

Build reusable strategies for recurring problems via autocontext's full multi-agent evolution loop.

### Flow

1. Parse: `--description "natural language problem"`, `--gens N` (default 3)
2. Call `autocontext_solve_scenario(description, generations=N)`
3. Poll `autocontext_solve_status(job_id)` until complete
4. Call `autocontext_solve_result(job_id)` → get skill package
5. Auto-import: `autocontext_import_package()` → lands in `.claude/skills/`
6. Notify via ntfy.sh (long-running)

### Example

```
/solve --description "Debug IIS application pool crashes on Windows Server" --gens 5
```

---

## Phase 5: `/self-eval` Command

Meta-command that evaluates Amplifier's own command outputs for continuous self-improvement.

### Flow

```
/self-eval brainstorm     — Score last brainstorm output against rubric
/self-eval create-plan    — Score last plan output
/self-eval all            — Batch evaluate recent command outputs
```

### Pre-built rubrics per command type

| Command | Rubric Dimensions |
|---------|------------------|
| `/brainstorm` | Clarity, completeness, YAGNI compliance, agent allocation accuracy, actionability |
| `/create-plan` | Task granularity, dependency ordering, agent matching, testability |
| `/subagent-dev` | Spec compliance, code quality, test coverage, zero-BS compliance |
| `/finish-branch` | Cleanup thoroughness, PR quality, no leftover artifacts |
| `/debug` | Root cause accuracy, hypothesis quality, fix minimality |

### Self-improvement flywheel

1. `/self-eval` scores a command's output → stores in autocontext
2. After N evaluations, patterns emerge in the playbook
3. Learnings export as skill notes to `.claude/skills/amplifier-self-improvement/`
4. `/recall` indexes those skills for future reference
5. Command prompts updated based on accumulated evidence

### Future: Phase 6 (not in this PR)

Observer hook runs `/self-eval` on SessionEnd for commands used that session — fully automated accumulation.

---

## Knowledge Bridge: AutoContext ↔ /recall

- `/recall` handles session history (what happened, when, decisions)
- AutoContext handles task knowledge (how to do X well, what strategies work)
- Bridge: autocontext exports skills to `.claude/skills/`, `/recall` can index those
- No duplication — each system owns its domain

---

## Files Changed

| File | Change |
|------|--------|
| `.mcp.json` | MODIFIED — add autocontext MCP server |
| `.claude/commands/evaluate.md` | NEW — evaluate command |
| `.claude/commands/improve.md` | NEW — improve command |
| `.claude/commands/solve.md` | NEW — solve command |
| `.claude/commands/self-eval.md` | NEW — self-eval command |

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|---------------|
| MCP setup | modular-builder | .mcp.json registration, dependency install |
| /evaluate command | modular-builder | Command file, task templates |
| /improve command | modular-builder | Command file, workflow integration |
| /solve command | modular-builder | Command file, async polling, ntfy |
| /self-eval command | modular-builder | Rubric definitions, command scoring |
| Validation | spec-reviewer | Verify all commands work end-to-end |
| Cleanup | post-task-cleanup | Final hygiene |

---

## Test Plan

- [ ] Verify autocontext MCP server starts: check `autocontext_capabilities()` returns version info
- [ ] `/evaluate code-review` with sample text — returns score breakdown
- [ ] `/improve code-review` with low-scoring output — score improves across rounds
- [ ] `/solve` with simple description — returns skill package
- [ ] `/self-eval brainstorm` — scores a brainstorm output against rubric
- [ ] Exported skills appear in `.claude/skills/` and are findable via `/recall`
