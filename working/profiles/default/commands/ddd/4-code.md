---
description: DDD Phase 4 - Implement and verify code (project:ddd)
argument-hint: [optional feedback or instructions]
allowed-tools: TodoWrite, Read, Write, Edit, MultiEdit, Grep, Glob, Task, Bash(*)
---

# DDD Phase 4: Implementation & Verification

Loading context:

@docs/document_driven_development/phases/04_code_implementation.md
@docs/document_driven_development/phases/05_testing_and_verification.md
@ai_working/ddd/code_plan.md

**CRITICAL**: Read ALL updated documentation - code must match exactly

User feedback/instructions: $ARGUMENTS

---

## Your Task: Implement Code & Test as User

**Goal**: Write code matching docs exactly, test as real user would, iterate until working

**This phase stays active until user confirms "all working" - iterate as long as needed**

---

## Phase 4A: Implementation

### For Each Chunk in Code Plan

#### Step 1: Load Full Context

Before implementing chunk:

- Read the code plan for this chunk
- Read ALL relevant documentation (the specs)
- Read current code in affected files
- Understand dependencies

**Context is critical** - don't rush this step

#### Step 2: Implement Exactly as Documented

**Code MUST match documentation**:

- If docs say "function returns X", code returns X
- If docs show config format, code parses that format
- If docs describe behavior, code implements that behavior
- Examples in docs must actually work

**If conflict arises**:

```
STOP ✋

Don't guess or make assumptions.

Ask user:
"Documentation says X, but implementing Y seems better because Z.
Should I:
a) Update docs to match Y
b) Implement X as documented
c) Something else?"
```

#### Step 3: Verify Chunk Works

After implementing chunk:

- Run relevant tests
- Check for syntax errors
- Basic smoke test
- Ensure no regressions

#### Step 4: Show Changes & Get Commit Authorization

**IMPORTANT**: Each commit requires EXPLICIT user authorization

Show user:

```markdown
## Chunk [N] Complete: [Description]

### Files Changed

[list with brief description of changes]

### What This Does

[plain English explanation]

### Tests

[which tests pass]

### Diff Summary
```

git diff --stat

```

### Proposed Commit
```

feat: [Chunk description]

[Detailed commit message based on code plan]

```

⚠️ **Request explicit authorization**:
"Ready to commit? (yes/no/show me diff first)"

If yes: commit with message
If no: ask what needs changing
If show diff: run `git diff` then ask again
```

#### Step 5: Move to Next Chunk

After successful commit, move to next chunk in plan.

Repeat Steps 1-4 for all chunks.

---

## Phase 4B: Testing as User Would

**After all implementation chunks complete**:

### Step 1: Actual User Testing

**Be the QA entity** - actually use the feature:

```bash
# Run the actual commands a user would run
amplifier run --with-new-feature

# Try the examples from documentation (they should work)
[copy exact examples from docs]

# Test error handling
[try invalid inputs]

# Test integration with existing features
[test it works with rest of system]
```

**Observe and record**:

- Actual output (what did you see?)
- Actual behavior (what happened?)
- Logs generated (what was logged?)
- Error messages (clear and helpful?)
- Performance (reasonable speed?)

### Step 2: Create Test Report

Write `ai_working/ddd/test_report.md`:

````markdown
# User Testing Report

Feature: [name]
Tested by: AI (as QA entity)
Date: [timestamp]

## Test Scenarios

### Scenario 1: Basic Usage

**Tested**: [what you tested]
**Command**: `[actual command run]`
**Expected** (per docs): [what docs say should happen]
**Observed**: [what actually happened]
**Status**: ✅ PASS / ❌ FAIL
**Notes**: [any observations]

### Scenario 2: Error Handling

**Tested**: [what you tested]
**Command**: `[actual command with invalid input]`
**Expected**: [error message from docs]
**Observed**: [actual error message]
**Status**: ✅ PASS / ❌ FAIL

[... continue for all scenarios]

## Documentation Examples Verification

### Example from docs/feature.md:123

```bash
[exact example from docs]
```
````

**Status**: ✅ Works as documented / ❌ Doesn't work
**Issue**: [if doesn't work, what's wrong]

[... test ALL examples from docs]

## Integration Testing

### With Feature X

**Tested**: [integration test]
**Status**: ✅ PASS / ❌ FAIL
**Notes**: [observations]

## Issues Found

### Issue 1: [Description]

**Severity**: High/Medium/Low
**What**: [description]
**Where**: [file:line or command]
**Expected**: [what should happen]
**Actual**: [what happens]
**Suggested fix**: [how to fix]

[... list all issues]

## Code-Based Test Verification

**Unit tests**:

```bash
make test
# [output]
```

Status: ✅ All passing / ❌ [N] failures

**Integration tests**:

```bash
make test-integration
# [output]
```

Status: ✅ All passing / ❌ [N] failures

**Linting/Type checking**:

```bash
make check
# [output]
```

Status: ✅ Clean / ❌ Issues found

## Summary

**Overall Status**: ✅ Ready / ⚠️ Issues to fix / ❌ Not working

**Code matches docs**: Yes/No
**Examples work**: Yes/No
**Tests pass**: Yes/No
**Ready for user verification**: Yes/No

## Recommended Smoke Tests for Human

User should verify:

1. **Basic functionality**:

   ```bash
   [command]
   # Should see: [expected output]
   ```

2. **Edge case**:

   ```bash
   [command]
   # Should see: [expected output]
   ```

3. **Integration**:
   ```bash
   [command]
   # Verify works with [existing feature]
   ```

[... provide 3-5 key smoke tests]

## Next Steps

[Based on status, recommend next action]

````

### Step 3: Address Issues Found

If testing revealed issues:
1. Note each issue clearly
2. Fix the code
3. Re-test
4. Update test report
5. Request commit authorization for fixes

**Stay in this phase until all issues resolved**

---

## Iteration Loop

**This phase stays active until user says "all working"**:

User provides feedback:
- "Feature X doesn't work as expected"
- "Error message is confusing"
- "Performance is slow"
- "Integration with Y is broken"

For each feedback:
1. Understand the issue
2. Fix the code
3. Re-test
4. Show changes
5. Request commit authorization
6. Repeat until user satisfied

---

## Using TodoWrite

Track implementation and testing tasks:

```markdown
# Implementation
- [ ] Chunk 1 of N
- [ ] Chunk 2 of N
...
- [ ] All chunks implemented

# Testing
- [ ] User scenario 1 tested
- [ ] User scenario 2 tested
...
- [ ] Documentation examples verified
- [ ] Integration tests passing
- [ ] Code tests passing
- [ ] Test report written
- [ ] All issues resolved
- [ ] User confirms working
````

---

## Agent Suggestions

**modular-builder** - For module implementation:

```
Task modular-builder: "Implement [chunk] according to code_plan.md
and documentation specifications"
```

**bug-hunter** - When issues found:

```
Task bug-hunter: "Debug [specific issue] found during testing"
```

**test-coverage** - For test suggestions:

```
Task test-coverage: "Suggest comprehensive test cases for [feature]"
```

---

## Important Notes

**Code must match docs EXACTLY**:

- Docs are the contract
- If code needs to differ, update docs first
- Examples in docs MUST work when copy-pasted
- Error messages should match what docs describe

**Each commit needs authorization**:

- Never assume user wants to commit
- Show clear summary of changes
- Get explicit "yes" before committing
- User can provide feedback instead

**Test as REAL user would**:

- Don't just run unit tests
- Actually use the CLI/feature
- Try the examples from docs
- See what real output looks like
- Experience what user will experience

**Stay in phase until working**:

- Don't rush to Phase 5
- Iterate as many times as needed
- Address all user feedback
- Only exit when user confirms "all working"

---

## Status Tracking

Maintain `ai_working/ddd/impl_status.md`:

```markdown
# Implementation Status

## Chunks

- [x] Chunk 1: [description] - Committed: [hash]
- [x] Chunk 2: [description] - Committed: [hash]
- [ ] Chunk 3: [description] - In progress
- [ ] Chunk 4: [description] - Not started

## Current State

Working on: [current chunk]
Last commit: [hash]
Tests passing: [yes/no]
Issues found: [count]

## User Feedback Log

### Feedback 1 (timestamp)

**User said**: [feedback]
**Action taken**: [what we did]
**Status**: Resolved/In progress

[... continue for all feedback]

## Next Steps

[What's next in this phase]
```

---

## When All Working

### Exit Message

```
✅ Phase 4 Complete: Implementation & Testing

All chunks implemented and committed.
All tests passing.
User testing complete.

Summary:
- Commits made: [count]
- Files changed: [count]
- Tests added: [count]
- Issues resolved: [count]

Test Report: ai_working/ddd/test_report.md

⚠️ USER CONFIRMATION

Is everything working as expected?

If YES, proceed to cleanup and finalization:

    /ddd:5-finish

If NO, provide feedback and we'll continue iterating in Phase 4.
```

## Process

- Ultrathink step-by-step, laying out assumptions and unknowns, use the TodoWrite tool to capture all tasks and subtasks.
  - VERY IMPORTANT: Make sure to use the actual TodoWrite tool for todo lists, don't do your own task tracking, there is code behind use of the TodoWrite tool that is invisible to you that ensures that all tasks are completed fully.
  - Adhere to the @ai_context/IMPLEMENTATION_PHILOSOPHY.md and @ai_context/MODULAR_DESIGN_PHILOSOPHY.md files.
- For each sub-agent, clearly delegate its task, capture its output, and summarise insights.
- Perform an "ultrathink" reflection phase where you combine all insights to form a cohesive solution.
- If gaps remain, iterate (spawn sub-agents again) until confident.
- Where possible, spawn sub-agents in parallel to expedite the process.

---

## Troubleshooting

**"Code doesn't match docs"**

- Read docs again carefully
- Implement exactly what docs describe
- If docs are unclear, ask user to clarify docs
- Don't implement what docs don't describe

**"Tests are failing"**

- Fix the implementation
- Don't change tests to pass
- Tests verify documented behavior
- If behavior changed, update docs first

**"User says 'not working'"**

- Ask specific questions: "What's not working?"
- Test that specific scenario
- Reproduce the issue
- Fix and re-test
- Show results to user

**"Too many issues found"**

- That's why we test!
- Better to find now than after release
- Fix them systematically
- Stay in phase until all resolved

**"Performance is slow"**

- Profile if needed
- Check for obvious inefficiencies
- But remember: working > fast initially
- Can optimize later if needed

---

Need help? Run `/ddd:0-help` for complete guide
