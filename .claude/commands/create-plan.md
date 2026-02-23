---
description: "Create comprehensive implementation plans with Amplifier agent allocation, TDD structure, and bite-sized tasks. Use when you have a spec or requirements for a multi-step task."
---

# Writing Plans

## Overview

Write comprehensive implementation plans assuming the engineer has zero context for our codebase and questionable taste. Document everything they need to know: which files to touch for each task, code, testing, docs they might need to check, how to test it. Give them the whole plan as bite-sized tasks. DRY. YAGNI. TDD. Frequent commits.

Assume they are a skilled developer, but know almost nothing about our toolset or problem domain. Assume they don't know good test design very well.

**Announce at start:** "I'm using the create-plan command to create the implementation plan."

**Before planning:** Gather context to avoid contradicting established architecture:
1. Search episodic memory for `knowledge_base.decisions` using the `mcp__plugin_episodic-memory_episodic-memory__search` tool
2. Search episodic memory for `knowledge_base.patterns` using the `mcp__plugin_episodic-memory_episodic-memory__search` tool
3. **If modifying existing code**, dispatch `agentic-search` to understand the current architecture before writing tasks:
   ```
   Task(subagent_type="agentic-search", model="haiku", max_turns=12, description="Understand [area] before planning", prompt="
     [specific question about how the code works that the plan depends on]
   ")
   ```
   This prevents plans that contradict existing patterns or miss dependencies. The agent uses ctags + Grep for fast symbol lookup and returns precise file:line references you can embed directly in task definitions.

**Context:** This should be run in a dedicated worktree (created by /brainstorm).

**Save plans to:** `docs/plans/YYYY-MM-DD-<feature-name>.md`
- (User preferences for plan location override this default)

## Scope Check

If the spec covers multiple independent subsystems, it should have been broken into sub-project specs during brainstorming. If it wasn't, suggest breaking this into separate plans — one per subsystem. Each plan should produce working, testable software on its own.

## File Structure

Before defining tasks, map out which files will be created or modified and what each one is responsible for. This is where decomposition decisions get locked in.

- Design units with clear boundaries and well-defined interfaces. Each file should have one clear responsibility.
- You reason best about code you can hold in context at once, and your edits are more reliable when files are focused. Prefer smaller, focused files over large ones that do too much.
- Files that change together should live together. Split by responsibility, not by technical layer.
- In existing codebases, follow established patterns. If the codebase uses large files, don't unilaterally restructure - but if a file you're modifying has grown unwieldy, including a split in the plan is reasonable.

This structure informs the task decomposition. Each task should produce self-contained changes that make sense independently.

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

## Plan Document Header

**Every plan MUST start with this header:**

```markdown
# [Feature Name] Implementation Plan

> **For Claude:** REQUIRED: Use /subagent-dev (if subagents available) or /execute-plan to implement this plan. Each task specifies its Agent — dispatch that Amplifier agent as the subagent for implementation. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** [One sentence describing what this builds]

**Architecture:** [2-3 sentences about approach]

**Tech Stack:** [Key technologies/libraries]

---
```

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

## Execution Handoff

After saving the plan:

**"Plan complete and saved to `docs/plans/<filename>.md`. Ready to execute?"**

**Execution path depends on harness capabilities:**

**If harness has subagents (Claude Code, etc.):**
- **REQUIRED:** Use /subagent-dev
- Do NOT offer a choice - subagent-driven is the standard approach
- Fresh subagent per task + two-stage review

**If harness does NOT have subagents:**
- Execute plan in current session using /execute-plan
- Batch execution with checkpoints for review

## Additional Guidance

$ARGUMENTS
