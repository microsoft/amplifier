---
description: "Execute implementation plans by dispatching specialized Amplifier agents per task with two-stage review. Fresh agent per task for clean context."
---

# Subagent-Driven Development

Execute plan by dispatching the Amplifier agent specified in each task, with two-stage review after each: spec compliance review first, then code quality review.

**Core principle:** Dispatch the right Amplifier specialist per task + two-stage review (spec then quality) = high quality, fast iteration

## When to Use

```dot
digraph when_to_use {
    "Have implementation plan?" [shape=diamond];
    "Tasks mostly independent?" [shape=diamond];
    "Stay in this session?" [shape=diamond];
    "subagent-driven-development" [shape=box];
    "executing-plans" [shape=box];
    "Manual execution or brainstorm first" [shape=box];

    "Have implementation plan?" -> "Tasks mostly independent?" [label="yes"];
    "Have implementation plan?" -> "Manual execution or brainstorm first" [label="no"];
    "Tasks mostly independent?" -> "Stay in this session?" [label="yes"];
    "Tasks mostly independent?" -> "Manual execution or brainstorm first" [label="no - tightly coupled"];
    "Stay in this session?" -> "subagent-driven-development" [label="yes"];
    "Stay in this session?" -> "executing-plans" [label="no - parallel session"];
}
```

**vs. Executing Plans (parallel session):**
- Same session (no context switch)
- Fresh Amplifier agent per task (specialist knowledge + no context pollution)
- Two-stage review after each task: spec compliance first, then code quality
- Faster iteration (no human-in-loop between tasks)

## Amplifier Agent Dispatch

Each task in the plan has an `Agent:` field. Use it as the `subagent_type` when dispatching:

1. Read the task's `Agent:` field (e.g., `modular-builder`, `bug-hunter`, `database-architect`)
2. **Dispatch using Task tool with `subagent_type` set to the Agent: field value.** Example: if the plan says `Agent: modular-builder`, call `Task(subagent_type="modular-builder", max_turns=15, description="Implement Task N: ...", prompt="...")`
   - **Turn budgets (always include `max_turns`):** Implementation agents: 15-20, review agents: 10-12, specialists: 12-15, quick tasks: 5-8
   - **If agent returns incomplete:** Resume with `Task(resume=agent_id, prompt="Continue your work...")` — max 3 resume cycles
3. Pass the full task text + context in the prompt (never make subagent read the plan file)
4. The agent brings domain expertise to the implementation — `modular-builder` builds clean modules, `bug-hunter` does hypothesis-driven debugging, `database-architect` designs schemas

**Review agents (from `.claude/AGENTS_CATALOG.md`):**
- Spec compliance review → `Task(subagent_type="test-coverage", ...)`
- Code quality review → `Task(subagent_type="zen-architect", ...)` in REVIEW mode
- Security-sensitive tasks → add `Task(subagent_type="security-guardian", ...)` as third reviewer
- Parallel review is OK: spec-compliance and security reviews are read-only, they can run concurrently

**After all tasks complete:**
- Dispatch `post-task-cleanup` agent for codebase hygiene
- **Memorize key decisions** made during implementation:
  - Architecture decisions → update DISCOVERIES.md or decision records
  - New patterns established → document in appropriate location
  - Domain terms clarified → update project glossary
- Then use `/finish-branch`

## Review Levels

Not every task needs full two-stage review. Match review depth to task risk:

**Level 1 — Self-review only** (simple, low-risk tasks):
- Task touches 1-2 files with clear spec
- No security implications
- Agent self-reviews, tests pass, commit → done
- Examples: rename, add field, simple CRUD, config change

**Level 2 — Spec compliance review** (standard tasks):
- Task touches multiple files or has integration concerns
- Dispatch `test-coverage` agent for spec compliance after implementation
- Skip separate code quality review
- Examples: new feature module, API endpoint, database migration

**Level 3 — Full two-stage review** (complex or security-sensitive tasks):
- Task involves security, auth, data handling, or architectural decisions
- Dispatch `test-coverage` for spec compliance, THEN `zen-architect` for code quality
- Add `security-guardian` for security-sensitive work
- Examples: auth flow, payment handling, data migration, public API

**How to choose:** Default to Level 2. Upgrade to Level 3 for security/architecture. Downgrade to Level 1 only when the task is trivially simple.

## The Process

```dot
digraph process {
    rankdir=TB;

    subgraph cluster_per_task {
        label="Per Task";
        "Read task Agent field, dispatch Amplifier agent (see Implementer Prompt Template)" [shape=box];
        "Agent asks questions?" [shape=diamond];
        "Answer questions, provide context" [shape=box];
        "Agent implements, tests, commits, self-reviews" [shape=box];
        "Determine review level (see Review Levels)" [shape=diamond style=filled fillcolor=lightyellow];
        "Level 1: self-review sufficient" [shape=box];
        "Level 2+: Dispatch test-coverage for spec review" [shape=box];
        "Spec compliant?" [shape=diamond];
        "Implementation agent fixes spec gaps" [shape=box];
        "Level 3: Dispatch zen-architect REVIEW mode" [shape=box];
        "Quality approved?" [shape=diamond];
        "Implementation agent fixes quality issues" [shape=box];
        "Mark task complete in TodoWrite" [shape=box];
    }

    "Read plan, extract all tasks with Agent fields, note context, create TodoWrite" [shape=box];
    "More tasks remain?" [shape=diamond];
    "Dispatch post-task-cleanup agent" [shape=box];
    "Use /finish-branch" [shape=box style=filled fillcolor=lightgreen];

    "Read plan, extract all tasks with Agent fields, note context, create TodoWrite" -> "Read task Agent field, dispatch Amplifier agent (see Implementer Prompt Template)";
    "Read task Agent field, dispatch Amplifier agent (see Implementer Prompt Template)" -> "Agent asks questions?";
    "Agent asks questions?" -> "Answer questions, provide context" [label="yes"];
    "Answer questions, provide context" -> "Read task Agent field, dispatch Amplifier agent (see Implementer Prompt Template)";
    "Agent asks questions?" -> "Agent implements, tests, commits, self-reviews" [label="no"];
    "Agent implements, tests, commits, self-reviews" -> "Determine review level (see Review Levels)";
    "Determine review level (see Review Levels)" -> "Level 1: self-review sufficient" [label="simple"];
    "Determine review level (see Review Levels)" -> "Level 2+: Dispatch test-coverage for spec review" [label="standard/complex"];
    "Level 1: self-review sufficient" -> "Mark task complete in TodoWrite";
    "Level 2+: Dispatch test-coverage for spec review" -> "Spec compliant?";
    "Spec compliant?" -> "Implementation agent fixes spec gaps" [label="no"];
    "Implementation agent fixes spec gaps" -> "Level 2+: Dispatch test-coverage for spec review" [label="re-review"];
    "Spec compliant?" -> "Level 3: Dispatch zen-architect REVIEW mode" [label="yes + complex"];
    "Spec compliant?" -> "Mark task complete in TodoWrite" [label="yes + standard"];
    "Level 3: Dispatch zen-architect REVIEW mode" -> "Quality approved?";
    "Quality approved?" -> "Implementation agent fixes quality issues" [label="no"];
    "Implementation agent fixes quality issues" -> "Level 3: Dispatch zen-architect REVIEW mode" [label="re-review"];
    "Quality approved?" -> "Mark task complete in TodoWrite" [label="yes"];
    "Mark task complete in TodoWrite" -> "More tasks remain?";
    "More tasks remain?" -> "Read task Agent field, dispatch Amplifier agent (see Implementer Prompt Template)" [label="yes"];
    "More tasks remain?" -> "Dispatch post-task-cleanup agent" [label="no"];
    "Dispatch post-task-cleanup agent" -> "Use /finish-branch";
}
```

## Dispatch Announcements

**Before every Task dispatch, output a visible status line to the user:**

```
>> Dispatching [agent-name] (model: [model]) for Task N: [short description]
>>   Review level: [1/2/3] | Files: [count] | Complexity: [simple/standard/complex]
```

For review dispatches:
```
>> Dispatching [reviewer-agent] (model: [model]) — [review type] review for Task N
```

This gives the user visibility into which specialist is handling what, at what cost tier, and what review depth applies. **Never dispatch silently.**

## Model Selection

Use the least powerful model that can handle each role.

**Claude Code** — map to the `model` parameter on the Task tool:

| Tier | Claude `model` | Gemini equivalent | When |
|------|---------------|-------------------|------|
| Fast | `haiku` | Flash | Mechanical implementation: 1-2 files, clear spec, config change |
| Balanced | `sonnet` | Pro | Standard: multi-file, integration, pattern matching, debugging |
| Deep | `opus` | Pro | Architecture/design/review: broad judgment, security review |

**Concrete mapping by agent type:**
- `modular-builder` with clear spec → `haiku` / Flash (upgrade to `sonnet` / Pro if multi-file)
- `bug-hunter` → `sonnet` / Pro (needs reasoning about root causes)
- `database-architect` → `sonnet` / Pro (schema design needs judgment)
- `test-coverage` (spec review) → `haiku` / Flash (checklist comparison)
- `zen-architect` (quality review) → `sonnet` / Pro (needs architecture judgment)
- `security-guardian` → `opus` / Pro (security requires deepest analysis)
- `post-task-cleanup` → `haiku` / Flash (mechanical cleanup)

**When to upgrade:** If a `haiku`/Flash agent returns BLOCKED or NEEDS_CONTEXT, re-dispatch with `sonnet`/Pro. If `sonnet`/Pro is blocked, try `opus`.

## Handling Implementer Status

Implementer subagents report one of four statuses. Handle each appropriately:

**DONE:** Proceed to spec compliance review.

**DONE_WITH_CONCERNS:** The implementer completed the work but flagged doubts. Read the concerns before proceeding. If the concerns are about correctness or scope, address them before review. If they're observations (e.g., "this file is getting large"), note them and proceed to review.

**NEEDS_CONTEXT:** The implementer needs information that wasn't provided. Provide the missing context and re-dispatch.

**BLOCKED:** The implementer cannot complete the task. Assess the blocker:
1. If it's a context problem, provide more context and re-dispatch with the same model
2. If the task requires more reasoning, re-dispatch with a more capable model
3. If the task is too large, break it into smaller pieces
4. If the plan itself is wrong, escalate to the human

**Never** ignore an escalation or force the same model to retry without changes. If the implementer said it's stuck, something needs to change.

## Prompt Templates

### Implementer Prompt Template

Use this template when dispatching an implementation agent. The `subagent_type` parameter comes from the task's `Agent:` field in the plan.

**CRITICAL: Use the Agent: field value as the `subagent_type` parameter.** This dispatches the specialized Amplifier agent, not a generic one.

```
Task tool:
  subagent_type: "general"
  description: "Implement Task N: [task name]"
  prompt: |
    You are the [agent-name from task's Agent: field] agent implementing Task N: [task name]

    ## IMMEDIATE ACTION

    **DO NOT PLAN.** The plan is already provided below.
    **EXECUTE IMMEDIATELY.** Do not waste tokens creating a new plan.

    ## Output Discipline

    When reporting back, keep your response concise to protect the caller's context:
    - List files created/modified with paths (not full contents)
    - Summarize what changed in each file (1-2 lines per file)
    - Include test results: pass/fail counts and command used
    - Include git commit hash from `git log -1 --format="%H %s"`
    - If a file is >200 lines, report the path and summary, not the full content
    - Keep total report under 200 lines

    ## Your Strengths

    [Brief description of what this agent specializes in, from .claude/AGENTS_CATALOG.md.
     Examples:
     - modular-builder: "You build self-contained, regeneratable modules following the bricks-and-studs philosophy."
     - database-architect: "You design clean schemas, optimize queries, and handle migrations."
     - bug-hunter: "You use hypothesis-driven debugging to find root causes systematically."
     - integration-specialist: "You handle external system integration with reliability and simplicity."]

    ## Task Description

    [FULL TEXT of task from plan - paste it here, don't make subagent read file]

    ## Context

    [Scene-setting: where this fits, dependencies, architectural context]

    ## Before You Begin

    1. **Style Check:** Read 1-2 related files to understand the project's style (e.g., naming conventions, event handlers like `OnClick` syntax). Mimic it exactly.
    2. **Clarify:** If you have questions about requirements, ask them now.

    ## Your Job

    1. Implement exactly what the task specifies
    2. Write tests (following TDD if task says to)
    3. Verify implementation works
    4. **Commit your work** (Required)
    5. **Verify Commit:** Run `git log -1` to prove the commit succeeded.
    6. Self-review (see below)
    7. Report back

    Work from: [directory]

    **While you work:** If you encounter something unexpected or unclear, **ask questions**.
    It's always OK to pause and clarify. Don't guess or make assumptions.

    ## Code Organization

    You reason best about code you can hold in context at once, and your edits are more
    reliable when files are focused. Keep this in mind:
    - Follow the file structure defined in the plan
    - Each file should have one clear responsibility with a well-defined interface
    - If a file you're creating is growing beyond the plan's intent, stop and report
      it as DONE_WITH_CONCERNS — don't split files on your own without plan guidance
    - If an existing file you're modifying is already large or tangled, work carefully
      and note it as a concern in your report
    - In existing codebases, follow established patterns. Improve code you're touching
      the way a good developer would, but don't restructure things outside your task.

    ## When You're in Over Your Head

    It is always OK to stop and say "this is too hard for me." Bad work is worse than
    no work. You will not be penalized for escalating.

    **STOP and escalate when:**
    - The task requires architectural decisions with multiple valid approaches
    - You need to understand code beyond what was provided and can't find clarity
    - You feel uncertain about whether your approach is correct
    - The task involves restructuring existing code in ways the plan didn't anticipate
    - You've been reading file after file trying to understand the system without progress

    **How to escalate:** Report back with status BLOCKED or NEEDS_CONTEXT. Describe
    specifically what you're stuck on, what you've tried, and what kind of help you need.
    The controller can provide more context, re-dispatch with a more capable model,
    or break the task into smaller pieces.

    ## Before Reporting Back: Self-Review

    Review your work with fresh eyes. Ask yourself:

    **Completeness:**
    - Did I fully implement everything in the spec?
    - Did I miss any requirements?
    - Are there edge cases I didn't handle?

    **Quality:**
    - Is this my best work?
    - Are names clear and accurate (match what things do, not how they work)?
    - Is the code clean and maintainable?

    **Discipline:**
    - Did I avoid overbuilding (YAGNI)?
    - Did I only build what was requested?
    - Did I follow existing patterns in the codebase?

    **Testing:**
    - Do tests actually verify behavior (not just mock behavior)?
    - Did I follow TDD if required?
    - Are tests comprehensive?

    If you find issues during self-review, fix them now before reporting.

    ## Report Format

    When done, report:
    - **Status:** DONE | DONE_WITH_CONCERNS | BLOCKED | NEEDS_CONTEXT
    - What you implemented (or what you attempted, if blocked)
    - What you tested and test results
    - Files changed
    - Self-review findings (if any)
    - Any issues or concerns

    Use DONE_WITH_CONCERNS if you completed the work but have doubts about correctness.
    Use BLOCKED if you cannot complete the task. Use NEEDS_CONTEXT if you need
    information that wasn't provided. Never silently produce work you're unsure about.
```

### Spec Compliance Reviewer Prompt Template

Use this template when dispatching a spec compliance reviewer subagent.

**Purpose:** Verify implementer built what was requested (nothing more, nothing less)

**Agent:** Dispatch `test-coverage` Amplifier agent (testing specialist with spec verification expertise)

```
Task tool (test-coverage):
  description: "Review spec compliance for Task N"
  prompt: |
    You are the test-coverage agent reviewing whether an implementation matches its specification.

    ## What Was Requested

    [FULL TEXT of task requirements]

    ## What Implementer Claims They Built

    [From implementer's report]

    ## CRITICAL: Do Not Trust the Report

    The implementer finished suspiciously quickly. Their report may be incomplete,
    inaccurate, or optimistic. You MUST verify everything independently.

    ## Output Discipline

    Keep your review concise to protect the caller's context:
    - State PASS or FAIL clearly at the top
    - List specific issues with file:line references
    - Do not reproduce full file contents in the review
    - For passing reviews, keep response under 50 lines
    - For failing reviews, keep response under 100 lines

    **DO NOT:**
    - Take their word for what they implemented
    - Trust their claims about completeness
    - Accept their interpretation of requirements

    **DO:**
    - Read the actual code they wrote
    - **Verify Persistence:** Check `git log -1` to ensure the work was actually committed.
    - Compare actual implementation to requirements line by line
    - Check for missing pieces they claimed to implement
    - Look for extra features they didn't mention

    ## Your Job

    Read the implementation code and verify:

    **Persistence Check:**
    - Did the implementer actually commit the code?
    - If files are modified but not committed, or if `git log` shows an old commit, **FAIL** the review immediately.

    **Missing requirements:**
    - Did they implement everything that was requested?
    - Are there requirements they skipped or missed?
    - Did they claim something works but didn't actually implement it?

    **Extra/unneeded work:**
    - Did they build things that weren't requested?
    - Did they over-engineer or add unnecessary features?
    - Did they add "nice to haves" that weren't in spec?

    **Misunderstandings:**
    - Did they interpret requirements differently than intended?
    - Did they solve the wrong problem?
    - Did they implement the right feature but wrong way?

    **Verify by reading code, not by trusting report.**

    Report:
    - Spec compliant (if everything matches after code inspection)
    - Issues found: [list specifically what's missing or extra, with file:line references]
```

### Code Quality Reviewer Prompt Template

Use this template when dispatching a code quality reviewer subagent.

**Purpose:** Verify implementation is well-built (clean, tested, maintainable)

**Agent:** Dispatch `zen-architect` Amplifier agent in REVIEW mode (architecture and quality specialist)

**Only dispatch after spec compliance review passes.**

```
Task tool (zen-architect):
  description: "Code quality review for Task N"
  prompt: |
    You are the zen-architect agent in REVIEW mode. Review the implementation
    for code quality, architecture alignment, and maintainability.

    WHAT_WAS_IMPLEMENTED: [from implementer's report]
    PLAN_OR_REQUIREMENTS: Task N from [plan-file]
    BASE_SHA: [commit before task]
    HEAD_SHA: [current commit]
    DESCRIPTION: [task summary]

    ## Your Review Focus

    **Architecture:**
    - Does this follow existing patterns in the codebase?
    - Are module boundaries clean?
    - Is the abstraction level appropriate?

    **Quality:**
    - Is the code clean and readable?
    - Are names clear and accurate?
    - Is complexity justified?

    **Simplicity:**
    - Could this be simpler without losing functionality?
    - Is there any unnecessary abstraction?
    - Does it follow YAGNI?

    **Testing:**
    - Do tests verify behavior (not implementation)?
    - Is test coverage adequate for the complexity?
    - Are tests maintainable?

    Report:
    - Strengths: [what's well done]
    - Issues: [Critical/Important/Minor with file:line references]
    - Assessment: Approved / Needs changes
```

**In addition to standard code quality concerns, the reviewer should check:**
- Does each file have one clear responsibility with a well-defined interface?
- Are units decomposed so they can be understood and tested independently?
- Is the implementation following the file structure from the plan?
- Did this implementation create new files that are already large, or significantly grow existing files? (Don't flag pre-existing file sizes — focus on what this change contributed.)

**Code reviewer returns:** Strengths, Issues (Critical/Important/Minor), Assessment

## Example Workflow

```
You: I'm using Subagent-Driven Development to execute this plan.

[Read plan file once: docs/plans/feature-plan.md]
[Extract all 5 tasks with full text, Agent fields, and context]
[Create TodoWrite with all tasks]

Task 1/5: Design auth module schema

>> Dispatching database-architect (model: sonnet) for Task 1: Design auth module schema
>>   Review level: 2 | Files: 3 | Complexity: standard

database-architect: "Should we use separate tables for roles and permissions, or a combined approach?"

You: "Separate tables — we need fine-grained permission assignment."

database-architect: "Got it. Implementing now..."
[Later] database-architect:
  Status: DONE
  - Created migration for users, roles, permissions tables
  - Added indexes for common query patterns
  - Tests: 4/4 passing
  - Committed

>> Dispatching test-coverage (model: haiku) — spec compliance review for Task 1
test-coverage: Spec compliant - schema matches requirements

[Mark Task 1 complete — Level 2 review passed, skipping quality review]

Task 2/5: Implement auth middleware

>> Dispatching modular-builder (model: haiku) for Task 2: Implement auth middleware
>>   Review level: 1 | Files: 1 | Complexity: simple

modular-builder: Status: DONE — implemented middleware with tests passing
[Mark Task 2 complete — Level 1 self-review sufficient]

Task 3/5: Add JWT token validation

>> Dispatching security-guardian (model: opus) for Task 3: Add JWT token validation
>>   Review level: 3 | Files: 4 | Complexity: complex (security-sensitive)

security-guardian: Status: DONE — implemented with OWASP best practices
>> Dispatching test-coverage (model: haiku) — spec compliance review for Task 3
>> Dispatching zen-architect (model: sonnet) — code quality review for Task 3
[Both reviews pass]
[Mark Task 3 complete]

...

>> Dispatching post-task-cleanup (model: haiku) for final hygiene pass
post-task-cleanup: Removed 2 unused imports, no other issues.

[Use /finish-branch]
Done!
```

## Advantages

**vs. Manual execution:**
- Specialist agents bring domain expertise per task
- Fresh context per task (no confusion)
- Parallel-safe (subagents don't interfere)
- Subagent can ask questions (before AND during work)

**vs. Executing Plans:**
- Same session (no handoff)
- Continuous progress (no waiting)
- Review checkpoints automatic

**Efficiency gains:**
- No file reading overhead (controller provides full text)
- Controller curates exactly what context is needed
- Agent brings domain expertise (database-architect knows schema patterns)
- Questions surfaced before work begins (not after)

**Quality gates:**
- Self-review catches issues before handoff
- Spec compliance via test-coverage agent (testing expert verifies completeness)
- Code quality via zen-architect REVIEW mode (architecture expert verifies quality)
- Security review via security-guardian (when applicable)
- Post-task-cleanup ensures hygiene
- Review loops ensure fixes actually work

**Cost:**
- More subagent invocations (implementer + 1-3 reviewers depending on review level)
- Controller does more prep work (extracting all tasks upfront)
- Review loops add iterations
- But catches issues early (cheaper than debugging later)

## Red Flags

**Never:**
- Start implementation on main/master branch without explicit user consent
- Skip reviews entirely (even Level 1 tasks need self-review; Level 2+ need spec compliance)
- Proceed with unfixed issues
- Dispatch multiple implementation subagents in parallel (conflicts)
- Make subagent read plan file (provide full text instead)
- Skip scene-setting context (subagent needs to understand where task fits)
- Ignore subagent questions (answer before letting them proceed)
- Accept "close enough" on spec compliance (spec reviewer found issues = not done)
- Skip review loops (reviewer found issues = implementer fixes = review again)
- Let implementer self-review replace actual review on Level 2+ tasks (both are needed)
- Use Level 1 (self-review only) for security-sensitive tasks — always upgrade to Level 3
- **Start code quality review before spec compliance is passed** (wrong order)
- Move to next task while either review has open issues
- Override the plan's Agent field without good reason

**If subagent asks questions:**
- Answer clearly and completely
- Provide additional context if needed
- Don't rush them into implementation

**If reviewer finds issues:**
- Implementer (same subagent) fixes them
- Reviewer reviews again
- Repeat until approved
- Don't skip the re-review

**If subagent fails task:**
- Dispatch fix subagent with specific instructions
- Don't try to fix manually (context pollution)

## Integration

**Required workflow commands:**
- **/worktree** - REQUIRED: Set up isolated workspace before starting
- **/create-plan** - Creates the plan this command executes (with Agent: fields)
- **/request-review** - Code review template for reviewer subagents
- **/finish-branch** - Complete development after all tasks

**Amplifier agents used:**
- **Implementation agents** - Per task's Agent: field (modular-builder, database-architect, etc.)
- **test-coverage** - Spec compliance reviewer
- **zen-architect** - Code quality reviewer (REVIEW mode)
- **security-guardian** - Security reviewer (when applicable)
- **post-task-cleanup** - Final hygiene pass

**Subagents should use:**
- **/tdd** - Subagents follow TDD for each task

**Alternative workflow:**
- **/execute-plan** - Use for parallel session instead of same-session execution
