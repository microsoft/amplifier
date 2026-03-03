---
description: "Formal code review request with self-review checklist. Use when completing tasks or before merging to verify work meets requirements."
---

# Requesting Code Review

Dispatch `zen-architect` agent (REVIEW mode) for automated self-review, then prepare for human review.

**Core principle:** Review early, review often.

## When to Request Review

**Mandatory:**
- After each task in subagent-driven development
- After completing major feature
- Before merge to main

**Optional but valuable:**
- When stuck (fresh perspective)
- Before refactoring (baseline check)
- After fixing complex bug

## How to Request

**1. Get git SHAs:**
```bash
BASE_SHA=$(git rev-parse HEAD~1)  # or origin/main
HEAD_SHA=$(git rev-parse HEAD)
```

**2. Automated self-review via zen-architect:**

Before requesting human review, dispatch `zen-architect` in REVIEW mode using the Task tool:

```
Task zen-architect (max_turns=12):
  Mode: REVIEW
  Review the code changes between {BASE_SHA} and {HEAD_SHA}.
  What was implemented: {WHAT_WAS_IMPLEMENTED}
  Requirements/plan: {PLAN_OR_REQUIREMENTS}

  Run: git diff --stat {BASE_SHA}..{HEAD_SHA}
  Run: git diff {BASE_SHA}..{HEAD_SHA}

  Review Checklist:

  Code Quality:
  - Clean separation of concerns?
  - Proper error handling?
  - Type safety (if applicable)?
  - DRY principle followed?
  - Edge cases handled?

  Architecture:
  - Sound design decisions?
  - Scalability considerations?
  - Performance implications?
  - Security concerns?

  Testing:
  - Tests actually test logic (not mocks)?
  - Edge cases covered?
  - Integration tests where needed?
  - All tests passing?

  Requirements:
  - All plan requirements met?
  - Implementation matches spec?
  - No scope creep?
  - Breaking changes documented?

  Production Readiness:
  - Migration strategy (if schema changes)?
  - Backward compatibility considered?
  - Documentation complete?
  - No obvious bugs?

  Output Format:

  ### Strengths
  [What's well done? Be specific.]

  ### Issues

  #### Critical (Must Fix)
  [Bugs, security issues, data loss risks, broken functionality]

  #### Important (Should Fix)
  [Architecture problems, missing features, poor error handling, test gaps]

  #### Minor (Nice to Have)
  [Code style, optimization opportunities, documentation improvements]

  For each issue:
  - File:line reference
  - What's wrong
  - Why it matters
  - How to fix (if not obvious)

  ### Recommendations
  [Improvements for code quality, architecture, or process]

  ### Assessment
  Ready to merge? [Yes/No/With fixes]
  Reasoning: [Technical assessment in 1-2 sentences]
```

**3. Fix issues from automated review:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later

**4. Request human review (if needed):**

Prepare a PR or review summary with:
- `{WHAT_WAS_IMPLEMENTED}` - What you just built
- `{PLAN_OR_REQUIREMENTS}` - What it should do
- `{BASE_SHA}` - Starting commit
- `{HEAD_SHA}` - Ending commit
- `{DESCRIPTION}` - Brief summary
- Automated review results and fixes applied

**5. Act on human feedback:**
- Fix Critical issues immediately
- Fix Important issues before proceeding
- Note Minor issues for later
- Push back if reviewer is wrong (with reasoning)

## Example

```
[Just completed Task 2: Add verification function]

You: Let me request code review before proceeding.

BASE_SHA=$(git log --oneline | grep "Task 1" | head -1 | awk '{print $1}')
HEAD_SHA=$(git rev-parse HEAD)

[Dispatch zen-architect in REVIEW mode]
  WHAT_WAS_IMPLEMENTED: Verification and repair functions for conversation index
  PLAN_OR_REQUIREMENTS: Task 2 from docs/plans/deployment-plan.md
  BASE_SHA: a7981ec
  HEAD_SHA: 3df7661
  DESCRIPTION: Added verifyIndex() and repairIndex() with 4 issue types

[zen-architect returns]:
  Strengths: Clean architecture, real tests
  Issues:
    Important: Missing progress indicators
    Minor: Magic number (100) for reporting interval
  Assessment: Ready to proceed

You: [Fix progress indicators]
[Continue to Task 3]
```

## Integration with Workflows

**Subagent-Driven Development (`/subagent-dev`):**
- Review after EACH task
- Catch issues before they compound
- Fix before moving to next task

**Executing Plans (`/subagent-dev`):**
- Review after each task (two-stage: spec + quality)
- Fix before moving to next task

**Ad-Hoc Development:**
- Review before merge
- Review when stuck

## Review Agent Rules

**DO:**
- Categorize by actual severity (not everything is Critical)
- Be specific (file:line, not vague)
- Explain WHY issues matter
- Acknowledge strengths
- Give clear verdict

**DON'T:**
- Say "looks good" without checking
- Mark nitpicks as Critical
- Give feedback on code you didn't review
- Be vague ("improve error handling")
- Avoid giving a clear verdict

## Red Flags

**Never:**
- Skip review because "it's simple"
- Ignore Critical issues
- Proceed with unfixed Important issues
- Argue with valid technical feedback

**If reviewer wrong:**
- Push back with technical reasoning
- Show code/tests that prove it works
- Request clarification

## Related Commands

- `/verify` - Verification before claiming work is complete
- `/finish-branch` - Finish development branch (merge, PR, cleanup)
- `/receive-review` - Handle incoming code review feedback
