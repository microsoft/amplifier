# Design Spec: Incorporate 7 Superpowers Patterns into Amplifier

**Date:** 2026-02-28
**Status:** Approved
**Source:** obra/superpowers v4.3.1

---

## Problem

Amplifier's workflow discipline has gaps:

1. Agents can skip brainstorming and proceed directly to implementation.
2. Implementation work starts on `main` without feature branches.
3. Self-review is single-pass — the implementer reviews their own work.
4. Agent descriptions are narrative prose, not optimized for LLM discovery (CSO).

The obra/superpowers project (v4.3.1) has proven patterns that address each of these gaps. This spec incorporates 7 of those patterns into Amplifier's existing skills and agents, enhancing discipline without breaking current workflows.

---

## Goal

Incorporate 7 specific patterns from superpowers into Amplifier. Each pattern targets one gap. Changes are additive: existing commands and agents remain functional; only new constraints and behaviors are added.

---

## Implementation Order

Lowest risk/effort first. Pattern 4 (two-stage review) is last because it is the most complex change.

| Order | Pattern | Rationale |
|-------|---------|-----------|
| 1 | Pattern 3 — Red Flags table | Pure documentation append; zero breakage risk |
| 2 | Pattern 5 — Mandatory worktrees | Shell check additions to 4 commands |
| 3 | Pattern 1 — EnterPlanMode intercept | New hook + marker file; isolated from command logic |
| 4 | Pattern 7 — CSO descriptions | Metadata-only rewrites across 34 agents |
| 5 | Pattern 2 — DOT flowcharts | New sections added to 4 commands |
| 6 | Pattern 6 — On-demand MCP | Documentation only; no config changes |
| 7 | Pattern 4 — Two-stage review | New agents + loop logic in /subagent-dev |

---

## Pattern 1: EnterPlanMode Intercept (Brainstorm Hard Gate)

### Purpose

Block Claude from entering Plan Mode when no brainstorm session has been validated for the current task. Forces the workflow `/brainstorm` → design validated → `/create-plan` → implementation.

### Files Changed

| File | Action |
|------|--------|
| `.claude/hooks/enforce-brainstorm.sh` | NEW — hook script |
| `.claude/settings.json` | MODIFY — register hook as PreToolUse on EnterPlanMode |

### Hook Script: `.claude/hooks/enforce-brainstorm.sh`

- Checks for the existence of `/tmp/amplifier-brainstorm-done`
- If the file is absent: exits with a non-zero code and prints the blocking message:
  ```
  Brainstorm required before entering Plan Mode.
  Run /brainstorm to validate the design, then try again.
  The marker file /tmp/amplifier-brainstorm-done will be set automatically.
  ```
- If the file is present: exits 0 (allow)

### Marker File Protocol

- `/brainstorm` writes `/tmp/amplifier-brainstorm-done` when the design is validated (at the end of the command, after user confirmation).
- `/create-plan` also writes `/tmp/amplifier-brainstorm-done` when a plan is finalized (covering cases where the user starts with /create-plan directly).
- The marker file is session-scoped (lives in `/tmp/`). A new terminal session requires a new brainstorm.

### Hook Registration in `settings.json`

```json
{
  "hooks": {
    "PreToolUse": [
      {
        "matcher": "EnterPlanMode",
        "hooks": [
          {
            "type": "command",
            "command": "bash .claude/hooks/enforce-brainstorm.sh"
          }
        ]
      }
    ]
  }
}
```

### Acceptance Criteria

1. Calling `EnterPlanMode` without running `/brainstorm` first produces the blocking message and does not enter Plan Mode.
2. After `/brainstorm` completes and writes the marker, `EnterPlanMode` proceeds without blocking.
3. After `/create-plan` completes and writes the marker, `EnterPlanMode` proceeds without blocking.
4. Deleting `/tmp/amplifier-brainstorm-done` causes the block to reactivate in the same session.

---

## Pattern 2: DOT Flowcharts as Process Specs

### Purpose

Replace ambiguous prose with authoritative DOT flowcharts in the 4 most complex commands. When the graph conflicts with prose, the graph wins.

### Commands Modified

| Command | What the Graph Captures |
|---------|------------------------|
| `/brainstorm` | Routing decision tree (problem → research → alternatives → validation → marker) |
| `/fix-bugs` | Multi-phase pipeline (investigate → reproduce → hypothesize → fix → verify) |
| `/subagent-dev` | Branch gate → task loop → two-stage review cycle |
| `/execute-plan` | Batch execution with review checkpoints |

### Section Format

Each modified command file receives a new section:

```markdown
## Process Graph (Authoritative)

> When this graph conflicts with prose, follow the graph.

```dot
digraph CommandName {
  // nodes and edges here
}
```
```

### Commands NOT Receiving Graphs

Simple or linear commands (`/commit`, `/verify`, `/post-task-cleanup`, `/debug`) do not receive graphs — they have no branching logic that warrants graph specification.

### Acceptance Criteria

1. All 4 command files contain a `## Process Graph (Authoritative)` section with a valid fenced DOT block.
2. The DOT syntax is valid (parseable by graphviz `dot -Tsvg`).
3. The instruction "When this graph conflicts with prose, follow the graph" appears verbatim in each section.

---

## Pattern 3: Red Flags Rationalization Table

### Purpose

Provide Claude with explicit self-check prompts that catch the 10 most common rationalization patterns that lead to skipping workflow steps.

### File Changed

| File | Action |
|------|--------|
| `AGENTS.md` | MODIFY — append new `## Red Flags` section |

### Table Content

The new section is appended to `AGENTS.md` without modifying any existing content.

```markdown
## Red Flags

If you catch yourself thinking any of the following, stop and apply the reality check before proceeding.

| If you're thinking... | Reality check |
|-----------------------|---------------|
| "This is simple, I'll just implement it directly" | Run /brainstorm first. Simplicity is confirmed after analysis, not assumed before it. |
| "I already know the codebase well enough" | Dispatch agentic-search anyway. Memory of past sessions is lossy. |
| "I'll write tests after the implementation" | /tdd exists for a reason. Tests first is not optional for non-trivial features. |
| "I'll skip the worktree, it's a small change" | Branch first always. Main is protected; there is no "small enough to skip". |
| "I can review my own code" | Two-stage review catches category errors that self-review misses. |
| "The user seems in a hurry, I'll skip brainstorming" | Rushing causes design mistakes that cost 10x the time saved. |
| "This refactor is obvious, no plan needed" | /create-plan takes 2 minutes. The blast radius of "obvious" refactors is routinely underestimated. |
| "I'll just fix this one file" | Check blast radius with grep first. Changes propagate in ways that are not always visible from one file. |
| "I tested it mentally, it should work" | /verify requires evidence, not claims. Mental testing has a well-documented failure rate. |
| "I'll clean up later" | Run /post-task-cleanup now. "Later" accumulates and becomes never. |
```

### Acceptance Criteria

1. `AGENTS.md` contains a `## Red Flags` section with the full 10-row table.
2. Existing AGENTS.md content is unchanged.
3. The section renders correctly as a markdown table.

---

## Pattern 4: Two-Stage Automated Review Loops

### Purpose

Eliminate single-pass self-review. After implementation, two independent review agents check the work before it is considered complete. The implementer cannot advance past review without PASS verdicts.

### Files Changed

| File | Action |
|------|--------|
| `.claude/agents/spec-reviewer.md` | NEW |
| `.claude/agents/code-quality-reviewer.md` | NEW |
| `.claude/commands/subagent-dev.md` | MODIFY — add two-stage review loop to task loop |

### Review Loop Logic (added to `/subagent-dev`)

After the implementer agent completes a task:

```
1. Dispatch spec-reviewer → verdict: PASS or FAIL + findings
2. If FAIL:
     implementer fixes based on findings
     spec-reviewer re-checks
     If FAIL again: escalate to user (do not loop a third time)
3. After spec-reviewer PASS:
   Dispatch code-quality-reviewer → verdict: PASS or FAIL + findings
4. If FAIL:
     implementer fixes based on findings
     code-quality-reviewer re-checks
     If FAIL again: escalate to user (do not loop a third time)
5. After code-quality-reviewer PASS: task is complete
```

**Loop cap:** Maximum 2 review cycles per reviewer per task. On the second consecutive FAIL, escalate to the user with both the findings and the implementer's attempted fixes.

**Trivial task exemption:** Single-line changes and documentation-only updates may skip review when the orchestrator explicitly marks the task as trivial. The orchestrator must justify the exemption in the task dispatch.

### Agent: `spec-reviewer.md`

**Role:** Verify that the implementation satisfies the task specification requirements.

**Inputs (provided in task prompt):**
- The original task specification
- List of files changed
- Diff or summary of changes

**Output format:**
```
VERDICT: PASS | FAIL
FINDINGS:
- [specific finding 1]
- [specific finding 2]
```

**Checks performed:**
- All specified requirements are addressed
- No specified requirements are missing
- No behavior contradicts the spec
- Edge cases mentioned in the spec are handled

### Agent: `code-quality-reviewer.md`

**Role:** Verify that the implementation follows project patterns, type safety, and test requirements.

**Inputs (provided in task prompt):**
- List of files changed
- Diff or summary of changes
- Project conventions (from AGENTS.md)

**Output format:**
```
VERDICT: PASS | FAIL
FINDINGS:
- [specific finding 1]
- [specific finding 2]
```

**Checks performed:**
- Type annotations are present and correct
- Code follows project style (line length, naming, imports)
- Tests exist for new logic (or exemption is justified)
- No unused imports, variables, or dead code introduced
- No placeholders (`NotImplementedError`, `TODO`, `pass` as stub) left in production paths

### Acceptance Criteria

1. Both new agent files exist and load without errors.
2. `/subagent-dev` dispatches spec-reviewer after each implementer completion.
3. `/subagent-dev` dispatches code-quality-reviewer after spec-reviewer PASS.
4. A second consecutive FAIL from either reviewer causes escalation to user, not a third loop.
5. Trivial task exemption is available and requires explicit orchestrator justification.

---

## Pattern 5: Mandatory Git Worktrees

### Purpose

Prevent implementation work from happening on `main` or `master`. A branch gate at the start of each implementation-phase command enforces this absolutely.

### Commands Modified

| Command | Action |
|---------|--------|
| `/subagent-dev` | Strengthen existing gate — make it a hard block |
| `/execute-plan` | Add branch gate |
| `/modular-build` | Add branch gate |
| `/parallel-agents` | Add branch gate |

### Branch Gate Implementation

Each modified command adds the following check at its start, before any other logic:

```bash
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null)
if [ "$CURRENT_BRANCH" = "main" ] || [ "$CURRENT_BRANCH" = "master" ]; then
  echo "ERROR: Cannot run on branch '$CURRENT_BRANCH'."
  echo "Create a feature branch first:"
  echo "  Option 1: /worktree  (recommended — isolated environment)"
  echo "  Option 2: git checkout -b feature/<name>"
  exit 1
fi
```

### Commands NOT Receiving Branch Gates

Read-heavy and auxiliary commands are unaffected:

- `/brainstorm` — research, no writes
- `/debug` — investigation, no writes
- `/verify` — read-only checks
- `/commit` — committing work already done on a branch
- `/fix-bugs` — investigation phase is read-heavy; branch creation is part of its own flow
- `/post-task-cleanup` — cleanup, not implementation

### Acceptance Criteria

1. Running `/subagent-dev`, `/execute-plan`, `/modular-build`, or `/parallel-agents` on `main` produces the blocking error message and halts execution.
2. Running the same commands on any non-main/master branch proceeds normally.
3. `/brainstorm`, `/debug`, `/verify`, and `/commit` are unaffected and run on any branch.

---

## Pattern 6: On-Demand MCP via CLI

### Purpose

Document the pattern for invoking additional MCP servers on-demand without polluting the always-loaded server configuration. Keeps the base configuration lean while making extension straightforward.

### Files Changed

| File | Action |
|------|--------|
| `AGENTS.md` | MODIFY — append `## On-Demand MCP` section |

### Tiered MCP Approach

| Tier | Servers | Configuration |
|------|---------|---------------|
| Always loaded | Episodic Memory, Chrome, Playwright | `~/.claude/settings.json` (unchanged) |
| On-demand | Additional servers as needed | `mcp` CLI invocation |
| Project-specific | Servers for a specific repo | Project `.claude/settings.json` |

### Section Content (appended to AGENTS.md)

```markdown
## On-Demand MCP

The always-loaded MCP servers (Episodic Memory, Chrome, Playwright) are sufficient for most tasks.
For specialized tasks requiring additional servers, use the `mcp` CLI rather than adding to the
always-loaded configuration.

### Pattern

Start an MCP server on-demand:
```bash
mcp add <server-name> -- <command>
```

Remove it when done:
```bash
mcp remove <server-name>
```

### Principles

- **Keep the base lean**: Only servers needed for every session belong in always-loaded config.
- **On-demand for specialized work**: Add servers for the duration of the task, then remove.
- **Project-specific servers**: Place in the project's `.claude/settings.json`, not global config.
- **Never modify global config for temporary needs**: Use `mcp add/remove` instead.
```

### Acceptance Criteria

1. `AGENTS.md` contains an `## On-Demand MCP` section with the tiered table and pattern.
2. No changes to any existing MCP server configuration files.
3. Always-loaded servers remain unchanged.

---

## Pattern 7: CSO-Optimized Agent Descriptions

### Purpose

Rewrite the `description` field in all 34 agent files to use keyword-dense action verbs and symptom keywords instead of human-readable narrative prose. This improves Claude's ability to select the correct agent (Claude Subagent Orchestration — CSO).

### Files Changed

| File | Action |
|------|--------|
| `.claude/agents/*.md` | MODIFY — rewrite `description` field in all 34 files |
| `.claude/AGENTS_CATALOG.md` | MODIFY — update descriptions to match |

### Description Rewrite Pattern

**Before (human-readable narrative):**
```yaml
description: Specialized debugging expert that systematically investigates and resolves software bugs
```

**After (CSO-optimized):**
```yaml
description: Debug errors, fix bugs, investigate failures, troubleshoot crashes, diagnose test failures, trace root causes, resolve exceptions
```

**Rules for rewriting:**
- Start with the primary action verb (Debug, Implement, Review, Design, etc.)
- Include 5–10 comma-separated action phrases
- Include symptom keywords that trigger natural agent selection
- Remove all adjectives describing the agent ("specialized", "expert", "powerful")
- Remove all meta-phrases ("that", "which", "designed to")
- Agent prompts, model settings, and all other fields remain unchanged

### All 34 Agent Files

The following agents receive description rewrites:

1. `agentic-search.md`
2. `ambiguity-guardian.md`
3. `amplifier-cli-architect.md`
4. `amplifier-expert.md`
5. `analysis-engine.md`
6. `animation-choreographer.md`
7. `api-contract-designer.md`
8. `art-director.md`
9. `bug-hunter.md`
10. `component-designer.md`
11. `concept-extractor.md`
12. `content-researcher.md`
13. `contract-spec-author.md`
14. `database-architect.md`
15. `design-system-architect.md`
16. `graph-builder.md`
17. `handoff-gemini.md`
18. `insight-synthesizer.md`
19. `integration-specialist.md`
20. `knowledge-archaeologist.md`
21. `layout-architect.md`
22. `modular-builder.md`
23. `module-intent-architect.md`
24. `pattern-emergence.md`
25. `performance-optimizer.md`
26. `post-task-cleanup.md`
27. `responsive-strategist.md`
28. `security-guardian.md`
29. `subagent-architect.md`
30. `test-coverage.md`
31. `visualization-architect.md`
32. `vmware-infrastructure.md`
33. `voice-strategist.md`
34. `zen-architect.md`

### Acceptance Criteria

1. All 34 agent files have their `description` field updated.
2. No `description` field contains narrative prose ("specialized", "expert", "designed to", "that").
3. Every `description` starts with an action verb.
4. All 34 agent prompts, model settings, and other fields are unchanged.
5. `.claude/AGENTS_CATALOG.md` descriptions match the updated agent file descriptions.

---

## Agent Allocation

| Phase | Agent | Responsibility |
|-------|-------|----------------|
| Codebase Research | `agentic-search` | Understand current command/agent structure before changes; read current hook registration format in settings.json |
| Architecture | `zen-architect` | Review integration approach for each pattern; flag conflicts with existing workflows |
| Implementation | `modular-builder` | Build hook script, modify commands, create new agent files, rewrite descriptions |
| Testing | `test-coverage` | Verify hooks work, verify gates block correctly, verify agents load |
| Cleanup | `post-task-cleanup` | Final hygiene pass after all patterns are implemented |

---

## Files Changed Summary

| File | Action | Pattern |
|------|--------|---------|
| `.claude/hooks/enforce-brainstorm.sh` | NEW | 1 |
| `.claude/settings.json` | MODIFY — add hook registration | 1 |
| `.claude/commands/brainstorm.md` | MODIFY — add marker write + DOT graph | 1, 2 |
| `.claude/commands/create-plan.md` | MODIFY — add marker write | 1 |
| `.claude/commands/fix-bugs.md` | MODIFY — add DOT graph | 2 |
| `.claude/commands/subagent-dev.md` | MODIFY — add DOT graph + two-stage review + strengthen branch gate | 2, 4, 5 |
| `.claude/commands/execute-plan.md` | MODIFY — add DOT graph + branch gate | 2, 5 |
| `.claude/commands/modular-build.md` | MODIFY — add branch gate | 5 |
| `.claude/commands/parallel-agents.md` | MODIFY — add branch gate | 5 |
| `AGENTS.md` | MODIFY — append Red Flags + On-demand MCP sections | 3, 6 |
| `.claude/agents/spec-reviewer.md` | NEW | 4 |
| `.claude/agents/code-quality-reviewer.md` | NEW | 4 |
| `.claude/agents/*.md` (all 34) | MODIFY — rewrite description field | 7 |
| `.claude/AGENTS_CATALOG.md` | MODIFY — update descriptions | 7 |

---

## Test Plan

### Pattern 1: EnterPlanMode Intercept

| Test | Expected Result |
|------|----------------|
| Call `EnterPlanMode` with no brainstorm marker present | Blocked with message directing to /brainstorm |
| Run `/brainstorm`, confirm completion, call `EnterPlanMode` | Proceeds without blocking |
| Run `/create-plan`, confirm completion, call `EnterPlanMode` | Proceeds without blocking |
| Delete `/tmp/amplifier-brainstorm-done`, call `EnterPlanMode` | Blocked again |

### Pattern 2: DOT Flowcharts

| Test | Expected Result |
|------|----------------|
| Open each of the 4 modified command files | `## Process Graph (Authoritative)` section present |
| Parse DOT blocks with `dot -Tsvg` | No syntax errors |
| Verify instruction text | "When this graph conflicts with prose, follow the graph" present verbatim |

### Pattern 3: Red Flags Table

| Test | Expected Result |
|------|----------------|
| Open `AGENTS.md` | `## Red Flags` section present with 10-row table |
| Diff existing content | No existing content modified |
| Render as markdown | Table renders correctly |

### Pattern 4: Two-Stage Review

| Test | Expected Result |
|------|----------------|
| Load `spec-reviewer.md` in Claude Code | Agent loads without errors |
| Load `code-quality-reviewer.md` in Claude Code | Agent loads without errors |
| Run `/subagent-dev` task, implementer completes | spec-reviewer is dispatched automatically |
| spec-reviewer returns FAIL twice | Escalation to user on second FAIL (no third loop) |
| spec-reviewer returns PASS | code-quality-reviewer is dispatched automatically |
| code-quality-reviewer returns FAIL twice | Escalation to user on second FAIL |
| Task marked trivial by orchestrator | Review loop skipped with logged justification |

### Pattern 5: Mandatory Worktrees

| Test | Expected Result |
|------|----------------|
| Run `/subagent-dev` on `main` | Blocked with branch error message |
| Run `/execute-plan` on `main` | Blocked with branch error message |
| Run `/modular-build` on `main` | Blocked with branch error message |
| Run `/parallel-agents` on `main` | Blocked with branch error message |
| Run each of the 4 commands on `feature/test` | Proceeds normally |
| Run `/brainstorm` on `main` | Unaffected, proceeds normally |
| Run `/debug` on `main` | Unaffected, proceeds normally |
| Run `/commit` on any branch | Unaffected, proceeds normally |

### Pattern 6: On-Demand MCP

| Test | Expected Result |
|------|----------------|
| Open `AGENTS.md` | `## On-Demand MCP` section present with tiered table |
| Check always-loaded MCP config | Episodic Memory, Chrome, Playwright unchanged |
| Check global `settings.json` | No new always-loaded servers added |

### Pattern 7: CSO Descriptions

| Test | Expected Result |
|------|----------------|
| Check all 34 agent `description` fields | No field contains "specialized", "expert", "designed to", or "that" |
| Check all 34 agent `description` fields | Every field starts with an action verb |
| Diff all 34 agent files against base | Only `description` line changed in each file |
| Open `AGENTS_CATALOG.md` | Descriptions match updated agent files |

---

## Constraints and Non-Goals

- **Non-goal:** Modify agent prompts or behavior — only metadata (`description`) changes in Pattern 7.
- **Non-goal:** Change always-loaded MCP server configuration in Pattern 6.
- **Non-goal:** Add review loops to any command other than `/subagent-dev` in Pattern 4.
- **Non-goal:** Add branch gates to read-only or auxiliary commands.
- **Constraint:** All changes are additive. No existing content is removed from AGENTS.md, only appended.
- **Constraint:** The marker file `/tmp/amplifier-brainstorm-done` is session-scoped and must not be persisted across terminal sessions.
- **Constraint:** Review loop cap is exactly 2 cycles. Escalation on the second FAIL is mandatory — do not increase the cap.
