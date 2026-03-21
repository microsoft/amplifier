---
description: Create implementation plans with agent allocation and TDD tasks. Use after brainstorm or with a spec.
effort: high
---
# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the create-plan command to create the implementation plan."

**Before planning:** Gather context to avoid contradicting established architecture:
1. Search episodic memory for `knowledge_base.decisions` using the `mcp__plugin_episodic-memory_episodic-memory__search` tool
2. Search episodic memory for `knowledge_base.patterns` using the `mcp__plugin_episodic-memory_episodic-memory__search` tool
3. **Strategy lookup:** Search recall for `Outcome:` entries matching the domain (e.g., `/recall Outcome: exchange`, `/recall Outcome: api-design`). If past outcomes exist, use them to inform agent and model tier selection:
   - Past retries > 1 at haiku → assign sonnet for similar tasks
   - Past score > 85 at sonnet → keep sonnet (don't over-provision to opus)
   - Past lesson mentions missing context → add that context to task prompts
4. **If modifying existing code**, dispatch `agentic-search` to understand the current architecture before writing tasks:
   ```
   Task(subagent_type="amplifier-core:agentic-search", model="haiku", max_turns=12, description="Understand [area] before planning", prompt="
     **READ-ONLY MODE: Use ONLY Read, Glob, Grep, LS, and search tools. Do NOT use Edit, Write, Bash, or any tool that modifies files.**

     [specific question about how the code works that the plan depends on]
   ")
   ```
   This prevents plans that contradict existing patterns or miss dependencies. The agent uses ctags + Grep for fast symbol lookup and returns precise file:line references you can embed directly in task definitions.

**Context:** This should be run in a dedicated worktree (created by /brainstorm).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Step 0: Scope Challenge

Before structuring the plan, challenge its premises. This step is NON-OPTIONAL.

### 0A. Existing Code Leverage
1. What existing code already partially or fully solves each sub-problem?
2. Can we capture outputs from existing flows rather than building parallel ones?
3. Is this plan rebuilding anything that already exists? If so, why rebuild instead of refactor?

### 0B. Complexity Check
If the plan touches more than 8 files or introduces more than 2 new classes/modules, that's a smell. Challenge whether the same goal can be achieved with fewer moving parts. Minimal diff: achieve the goal with the fewest new abstractions.

### 0C. Mode Selection
Present the user with three options:

**A) SCOPE EXPANSION** — Push scope UP. "What would make this 10x better for 2x the effort?" Dream big, find delight opportunities, build for the 12-month vision. Use when exploring new product territory.

**B) HOLD SCOPE** (default) — Maximum rigor within the stated scope. Bulletproof the plan — catch every failure mode, test every edge case. Do not silently reduce OR expand. Use for most feature work.

**C) SCOPE REDUCTION** — Surgeon mode. Cut to the absolute minimum viable version that delivers core user value. Ruthlessly defer everything else. Use when time-pressured or scope-crept.

**Critical:** Once the user selects a mode, COMMIT to it. Do not silently drift. If EXPANSION, don't argue for less work later. If REDUCTION, don't sneak scope back in.

If the user doesn't explicitly choose, default to HOLD SCOPE and note this.

After scope challenge, proceed to Subsystem Decomposition Check below to verify the spec doesn't need splitting into separate plans.

## Subsystem Decomposition Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

### Task Decomposition: Vertical Slices (Tracer Bullets)

When breaking features into tasks, use **vertical slices** that cut through all layers, not horizontal slices that build one layer at a time.

**Horizontal (AVOID):**
```
Task 1: Build all API endpoints
Task 2: Build all database migrations
Task 3: Build all UI components
Task 4: Connect everything together
```

**Vertical (REQUIRED):**
```
Task 1: One endpoint + its migration + its UI → working end-to-end
Task 2: Next endpoint + its migration + its UI → working end-to-end
Task 3: Remaining endpoints following the pattern
```

**Why this matters for agents:** Each vertical slice:
- Validates architectural assumptions early (the first slice proves the pattern)
- Produces testable, demoable output at every step
- Gives agents a fresh context window between slices
- Allows the pattern established in slice 1 to be followed in slices 2-N
- Prevents "big bang integration" where nothing works until everything works

**Rules:**
1. The FIRST task should be the thinnest possible end-to-end slice — a "tracer bullet" that proves the architecture
2. Each subsequent task expands from the proven pattern
3. Every task should leave the codebase in a working, testable state
4. If a task only touches one layer (e.g., "add all migrations"), split it into vertical slices instead
5. Mark the first tracer-bullet task as `[TRACER]` — advisory marker indicating highest priority. The orchestrator or user should execute this task first before parallelizing remaining work

### Error Map (for plans with new codepaths)

When the plan introduces new services, API endpoints, external integrations, or data flows, require an error map:

**What Can Go Wrong:**
```
CODEPATH                | WHAT CAN FAIL           | ERROR TYPE
------------------------|-------------------------|------------------
ExternalAPI.call()      | Timeout                 | TimeoutError
                        | Rate limited (429)      | RateLimitError
                        | Malformed response      | ParseError
Database.write()        | Unique constraint       | ConflictError
                        | Connection lost         | ConnectionError
```

**Shadow Path Tracing:** Every data flow has a happy path plus three shadow paths: nil/null input, empty input, and upstream error. All four must be addressed in the plan.

**Rescue Status:** For each error type, the plan must specify: Is it handled? What happens? What does the user see? Any unhandled error is a plan gap.

Skip this section for plans that only modify existing codepaths without introducing new failure modes.

## Amplifier Agent Assignment

Each task gets an `Agent:` field specifying which Amplifier agent will handle it during execution. Read `.claude/AGENTS_CATALOG.md` for the full catalog (31 agents across 5 categories).

**Auto-assign by scanning the task description:**

| Task Type | Agent | When |
|-----------|-------|------|
| Research/explore | `agentic-search` | Understanding code before changing it, finding all callers, tracing flows |
| Architecture | `zen-architect` | System design, module boundaries, ANALYZE/ARCHITECT mode |
| Implementation | `modular-builder` | Build, create, add — the default for writing code |
| Test | `test-coverage` | Test strategy, coverage analysis, test case design |
| Fix/debug | `bug-hunter` | Errors, failures, unexpected behavior |
| Security | `security-guardian` | Auth, secrets, OWASP, vulnerability assessment |
| API | `api-contract-designer` | Endpoint contracts, REST/GraphQL specs |
| Database | `database-architect` | Schema, migrations, query optimization |
| UI | `component-designer` | Frontend components, visual elements |
| Integration | `integration-specialist` | External APIs, MCP servers, dependencies |
| Performance | `performance-optimizer` | Bottlenecks, profiling, optimization |
| Cleanup | `post-task-cleanup` | Dead code, hygiene, lint fixes after task completion |

When in doubt, use `modular-builder` for building and `bug-hunter` for fixing.

**Research tasks come first.** When a plan modifies existing code, the first task(s) should use `agentic-search` to map the current architecture. This gives subsequent implementation agents precise file:line targets instead of vague "find and modify" instructions.

**Review tasks use dedicated agents:**
- Spec compliance review → `test-coverage`
- Code quality review → `zen-architect` (REVIEW mode)
- Security review → `security-guardian`
- Final cleanup → `post-task-cleanup`

## Bite-Sized Task Granularity

**Each step is one action (2-5 minutes):**
- "Write the failing test" - step
- "Run it to make sure it fails" - step
- "Implement the minimal code to make the test pass" - step
- "Run the tests and make sure they pass" - step
- "Commit" - step

### Diagrams

For plans involving any of the following, include ASCII diagrams:
- **Data flows**: Show input → validation → transform → persist → output
- **State machines**: Show all states and transitions (including invalid ones)
- **Dependency graphs**: Show new components and their relationships to existing ones
- **Processing pipelines**: Show multi-step flows with error/retry paths

Diagram maintenance: when the plan modifies code that has existing diagrams (in comments, docs, or architecture files), flag stale diagrams that need updating as part of the plan.

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

## Pre-Dispatch Prompt Quality Gate

When generating task prompts for the plan (the text each agent will receive), apply the same silent quality check used by `/subagent-dev`:

| Dimension | Question | Target |
|-----------|----------|--------|
| Clarity | Is the task unambiguous? Could the agent misinterpret scope? | >= 7/10 |
| Specificity | Are file paths, function names, and expected behavior concrete? | >= 7/10 |
| Structure | Does it have: goal, context, constraints, success criteria? | >= 7/10 |
| Constraints | Are boundaries explicit (what NOT to do, what's out of scope)? | >= 7/10 |

**Average >= 7:** write to plan as-is.
**Average 5-6:** strengthen before writing — add missing file paths, boundaries, or examples.
**Average < 5:** rewrite the task prompt — it will produce poor agent output and waste a dispatch cycle.

Vague task prompts cause agent retries downstream which cost more than the time spent strengthening the prompt now.

This is a mental checkpoint, not a visible output. Silent unless it changes the plan content.

---

## Context-Efficient Plan Generation

For plans with 5+ tasks, delegate the heavy generation work to a subagent to protect the main context window:

```
Task(subagent_type="general-purpose", model="sonnet", description="Generate implementation plan for [feature]", prompt="
  You are writing an implementation plan. Follow these instructions EXACTLY.

  ## Spec Document
  Read the spec at: [spec file path]

  ## Agent Mapping
  Read the agent mapping at: .claude/AGENTS_CATALOG.md

  ## Plan Template
  [paste the full plan document header template and task structure template from this command]

  ## Requirements
  1. Create a task for each change in the spec's 'Files Changed' section
  2. Assign Agent: field to each task based on the agent mapping
  3. Include exact file paths for all Create/Modify/Test entries
  4. Write complete code for each step (not placeholders)
  5. Include TDD steps: write failing test, verify failure, implement, verify pass, commit
  6. Add review tasks where the spec's Agent Allocation specifies reviewers
  7. Write the plan to: [output path]
  8. Commit: git add <file> && git commit -m 'docs: add <feature> implementation plan'
  9. Return: file path, git commit hash, task count, and a 200-word summary of what each task covers
")
```

For plans with <5 tasks, generate in-context as before (the overhead is acceptable).

After receiving the subagent's summary, present it to the user: "Plan complete with N tasks. [summary]. Ready to execute?"

## Task Structure

### Research Task (when modifying existing code)

```markdown
### Task 0: Understand [area] architecture

**Agent:** agentic-search

**Question:** How does [feature/module] work end-to-end? What files handle [specific concern]?

**Expected output:** Key Files table with file:line references, architecture narrative, dependency map.
**Use results in:** Tasks 1-N file paths and modification targets.
```

Research tasks always come before implementation tasks. Their output gives subsequent agents precise targets.

### Implementation Task

```markdown
### Task N: [Component Name]

**Agent:** [agent-name from AGENTS_CATALOG.md]
**Model:** [optional: haiku | sonnet | opus — omit to use default tier table]

**Files:**
- Create: `exact/path/to/file.py`
- Modify: `exact/path/to/existing.py:123-145`
- Test: `tests/exact/path/to/test.py`

- [ ] **Step 1: Write the failing test**

` ` `python
def test_specific_behavior():
    result = function(input)
    assert result == expected
` ` `

- [ ] **Step 2: Run test to verify it fails**

Run: `pytest tests/path/test.py::test_name -v`
Expected: FAIL with "function not defined"

- [ ] **Step 3: Write minimal implementation**

` ` `python
def function(input):
    return expected
` ` `

- [ ] **Step 4: Run test to verify it passes**

Run: `pytest tests/path/test.py::test_name -v`
Expected: PASS

- [ ] **Step 5: Commit**

` ` `bash
git add tests/path/test.py src/path/file.py
git commit -m "feat: add specific feature"
` ` `
```

## Review Tasks

Include explicit review tasks in the plan for security-sensitive or complex implementations:

```markdown
### Task N+1: Security Review

**Agent:** security-guardian

**Scope:** Review Tasks 1-N for OWASP Top 10, secret detection, auth patterns
**Output:** Security findings with file:line references
**Action:** If issues found, create fix tasks and re-review
```

## Remember
- Exact file paths always — verify Modify targets exist (glob) and Create targets don't already exist
- Complete code in plan (not "add validation")
- Exact commands with expected output
- Reference relevant skills with @ syntax
- DRY, YAGNI, TDD, frequent commits
- Every task has an Agent: field

## TaskDAG

After writing the full plan, generate a structured TaskDAG section at the end of the plan document. This enables `/subagent-dev` to auto-compute execution waves and make confidence-based dispatch decisions.

### Instructions for Generating the TaskDAG

Append this section to the plan document, after all task definitions:

```markdown
## TaskDAG

```json
{
  "tasks": [
    {"id": "0.1", "name": "Understand current architecture", "agent": "agentic-search", "depends_on": [], "confidence": 0.7, "parallel": true},
    {"id": "1.1", "name": "Write sync script", "agent": "modular-builder", "depends_on": ["0.1"], "confidence": 0.9, "parallel": true},
    {"id": "1.2", "name": "Run sync", "agent": "modular-builder", "depends_on": ["1.1"], "confidence": 0.95, "parallel": false}
  ],
  "critical_path": ["0.1", "1.1", "1.2"],
  "max_parallelism": 3,
  "total_tasks": 8,
  "estimated_minutes": 45
}
```
```

### Field Definitions

Each task entry:
- `id`: Task identifier matching the plan's `### Task N` heading (e.g., `"1.1"`, `"2.3"`)
- `name`: Short task name (3-6 words)
- `agent`: Amplifier agent slug from the task's `Agent:` field
- `depends_on`: Array of task IDs that must complete before this task starts. Empty array `[]` means no dependencies.
- `confidence`: Float 0.0–1.0 scoring how well-understood this task is before implementation begins
- `parallel`: Boolean — `true` if this task can run in parallel with others in its wave, `false` if it must run alone

### Confidence Scoring Rules

| Task type | Confidence |
|-----------|-----------|
| Greenfield (no existing code to understand) | 0.6 |
| Research/explore tasks (`agentic-search`) | 0.7 |
| Implementation with spec and known patterns | 0.9 |
| Config changes, renames, documentation | 0.95 |
| Implementation on unfamiliar codebase (no prior research) | 0.5 |

**Low confidence (< 0.5):** Precede with an `agentic-search` task to raise confidence before implementation.

### DAG-Level Fields

- `critical_path`: Ordered array of task IDs forming the longest dependency chain (blocking path)
- `max_parallelism`: Count of the largest set of tasks with no mutual dependencies (max tasks that can run simultaneously)
- `total_tasks`: Total task count across all waves
- `estimated_minutes`: Sum of estimated time per task (research: 10m, simple impl: 15m, complex impl: 30m, review: 10m)

### Example (3-task plan)

```json
{
  "tasks": [
    {"id": "0.1", "name": "Map auth module architecture", "agent": "agentic-search", "depends_on": [], "confidence": 0.7, "parallel": true},
    {"id": "1.1", "name": "Add JWT validation middleware", "agent": "modular-builder", "depends_on": ["0.1"], "confidence": 0.9, "parallel": false},
    {"id": "1.2", "name": "Write integration tests", "agent": "test-coverage", "depends_on": ["1.1"], "confidence": 0.9, "parallel": false}
  ],
  "critical_path": ["0.1", "1.1", "1.2"],
  "max_parallelism": 1,
  "total_tasks": 3,
  "estimated_minutes": 55
}
```

**Note:** The TaskDAG is a machine-readable companion to the human-readable plan. Keep them in sync — if you add/remove/reorder tasks, update the DAG.

---

### Plan Quality Checklist

Before finalizing the plan, verify:
- [ ] **Zero silent failures** — every failure mode is visible to the system, team, or user
- [ ] **Every error has a name** — specific types, not generic "handle errors"
- [ ] **Observability is scope** — new codepaths have logs, metrics, or traces planned
- [ ] **Nothing deferred is vague** — anything deferred has a concrete TODO with context
- [ ] **Scope mode honored** — no silent drift from the chosen mode

## Plan Validation (before presenting to user)

After generating the plan, validate it against the spec/requirements:

1. **Dispatch a reviewer** (haiku, read-only, 8 turns) to check:
   - Does every requirement in the spec map to at least one task?
   - Are there tasks that don't trace back to any requirement? (scope creep)
   - Are there requirements with no corresponding task? (gaps)

2. **If gaps found:** Add missing tasks to cover them. If scope creep found: flag for user decision (keep or cut).

3. **Print coverage matrix:**
```
Requirement → Task Mapping:
  ✓ Auth endpoint → Task 2
  ✓ Database schema → Task 1
  ✗ Error handling → NO TASK (gap!)
  ? Rate limiting → Task 5 (not in spec — scope creep?)
```

Skip this step if no spec/requirements document was provided (ad-hoc plans).

## Plan Review Loop

After completing each chunk of the plan:

1. Dispatch plan-document-reviewer subagent (see plan-document-reviewer-prompt.md) for the current chunk
   - Provide: chunk content, path to spec document
2. If Issues Found:
   - Fix the issues in the chunk
   - Re-dispatch reviewer for that chunk
   - Repeat until Approved
3. If Approved: proceed to next chunk (or execution handoff if last chunk)

**Chunk boundaries:** Use `## Chunk N: <name>` headings to delimit chunks. Each chunk should be ≤1000 lines and logically self-contained.

**Review loop guidance:**
- Same agent that wrote the plan fixes it (preserves context)
- If loop exceeds 5 iterations, surface to human for guidance
- Reviewers are advisory - explain disagreements if you believe feedback is incorrect

## Session Naming

After saving the plan, rename this session to reflect the topic:

/rename plan: <topic>

Derive `<topic>` (2-4 words) from the feature name. Example: `/rename plan: auth-token-refresh`

If `/rename` is unavailable, skip this step.

## Plan Cache Integration

Before generating a new plan, check the cache for a similar existing plan:

```bash
AMPLIFIER_HOME="${AMPLIFIER_HOME:-$([ -d /opt/amplifier ] && echo /opt/amplifier || echo /c/claude/amplifier)}"
uv run python "$AMPLIFIER_HOME/scripts/plan-cache.py" lookup --prompt "$SPEC_SUMMARY"
```

Where `$SPEC_SUMMARY` is a short (1-3 sentence) summary of what you are about to plan.

**If a match is found (>70% similarity), present to the user:**

> A similar plan was found in the cache (N% match: "[cached plan title]").
> How would you like to proceed?
> - **A) Adapt this plan** — Load the cached plan and modify it for the current spec
> - **B) Generate fresh** — Ignore the cache and generate a new plan from scratch
> - **C) View cached plan first** — Show the cached plan before deciding

Wait for user choice before proceeding.

**After the plan is saved**, store it in the cache:

```bash
uv run python "$AMPLIFIER_HOME/scripts/plan-cache.py" store --plan "$PLAN_PATH" --prompt "$SPEC_SUMMARY"
```

Where `$PLAN_PATH` is the path where the plan was saved (e.g., `docs/plans/2026-03-21-feature-name.md`).

---

## Execution Handoff

After saving the plan:

**"Plan complete and saved to `docs/plans/<filename>.md`. Ready to execute?"**

**Execution path depends on harness capabilities:**

**If harness has subagents (Claude Code, etc.):**
- **REQUIRED:** Use /subagent-dev
- Do NOT offer a choice - subagent-driven is the standard approach
- Fresh subagent per task + two-stage review

**If harness does NOT have subagents:**
- Execute plan in current session using /subagent-dev
- Batch execution with checkpoints for review

### Write Brainstorm Marker

After saving the plan and before handing off to execution, write the brainstorm marker file to unlock Plan Mode:

```bash
touch /tmp/amplifier-brainstorm-done
```

This covers the case where the user starts with /create-plan directly (skipping /brainstorm). The marker file is session-scoped.

## Additional Guidance

$ARGUMENTS
