---
description: DDD Phase 3 - Plan code implementation (project:ddd)
argument-hint: [optional override instructions]
allowed-tools: TodoWrite, Read, Grep, Glob, Task, Bash(git diff:*), Bash(make check:*)
---

# DDD Phase 3: Code Planning

Loading context:

@docs/document_driven_development/phases/03_implementation_planning.md
@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md
@ai_working/ddd/plan.md

**CRITICAL**: Read ALL updated documentation - these are now the specifications

Override instructions: $ARGUMENTS

---

## Your Task: Plan Complete Code Implementation

**Goal**: Assess current code, plan all changes to match new documentation

**Output**: `ai_working/ddd/code_plan.md` - Detailed implementation specification

---

## Phase 3 Steps

### 1. Read Updated Documentation (The Specifications)

**The docs you updated in Phase 2 are now the SPEC**:

Read ALL documentation that describes what the code should do:

- User-facing docs (how it works)
- API documentation (interfaces)
- Configuration docs (settings)
- Architecture docs (design)

This is what the code MUST implement.

### 2. Code Reconnaissance

For each code file in the plan (Phase 1):

**Understand current state**:

- Read the existing code
- Understand current architecture
- Identify current behavior
- Note existing tests

**Gap analysis**:

- What does code do now?
- What should code do (per docs)?
- What's missing?
- What needs to change?
- What needs to be removed?

Use Grep and Glob to explore related code:

```bash
# Find all references to a module
grep -r "import module_name"

# Find all files in a package
glob "src/package/**/*.py"
```

### 3. Create Implementation Specification

Write `ai_working/ddd/code_plan.md`:

```markdown
# Code Implementation Plan

Generated: [timestamp]
Based on: Phase 1 plan + Phase 2 documentation

## Summary

[High-level description of what needs to be implemented]

## Files to Change

### File: src/module1.py

**Current State**:
[What the code does now]

**Required Changes**:
[What needs to change to match documentation]

**Specific Modifications**:

- Add function `do_something()` - [description]
- Modify function `existing_func()` - [changes needed]
- Remove deprecated code - [what to remove]

**Dependencies**:
[Other files this depends on, if any]

**Agent Suggestion**: modular-builder

---

### File: src/module2.py

[... repeat for EVERY code file]

## Implementation Chunks

Break implementation into logical, testable chunks:

### Chunk 1: Core Interfaces / Data Models

**Files**: [list]
**Description**: [what this chunk does]
**Why first**: [usually: other chunks depend on these]
**Test strategy**: [how to verify]
**Dependencies**: None
**Commit point**: After unit tests pass

### Chunk 2: Business Logic

**Files**: [list]
**Description**: [what this chunk does]
**Why second**: [dependency reasoning]
**Test strategy**: [how to verify]
**Dependencies**: Chunk 1
**Commit point**: After integration tests pass

### Chunk 3: [Continue...]

[... continue until all changes covered]

## New Files to Create

If any new files needed:

### File: src/new_module.py

**Purpose**: [why needed]
**Exports**: [public interface]
**Dependencies**: [what it imports]
**Tests**: tests/test_new_module.py

## Files to Delete

If any files should be removed:

### File: src/deprecated.py

**Reason**: [why removing]
**Migration**: [how existing users migrate, if applicable]

## Agent Orchestration Strategy

### Primary Agents

**modular-builder** - For module implementation:
```

Task modular-builder: "Implement [module] according to spec in
code_plan.md and updated documentation"

```

**bug-hunter** - If issues arise:
```

Task bug-hunter: "Debug issue with [specific problem]"

```

**test-coverage** - For test planning:
```

Task test-coverage: "Suggest comprehensive tests for [module]"

```

### Sequential vs Parallel

**Sequential** (dependencies between chunks):
```

Chunk 1 → Chunk 2 → Chunk 3

```

**Parallel** (independent chunks):
```

Chunk 1 ⎤
Chunk 2 ⎥ → Merge
Chunk 3 ⎦

````

Use sequential for this project: [reason]

## Testing Strategy

### Unit Tests to Add

**File: tests/test_module1.py**
- Test `function_a()` - [what to verify]
- Test `function_b()` - [what to verify]

[... for each module]

### Integration Tests to Add

**File: tests/integration/test_feature.py**
- Test end-to-end flow - [description]
- Test error handling - [cases]

### User Testing Plan

How will we actually test as a user?

**Commands to run**:
```bash
# Test basic functionality
command --flag value

# Test error handling
command --invalid

# Test integration
command1 && command2
````

**Expected behavior**:
[What user should see]

## Philosophy Compliance

### Ruthless Simplicity

- [How this implementation stays simple]
- [What we're NOT doing (YAGNI)]
- [Where we're removing complexity]

### Modular Design

- [Clear module boundaries]
- [Well-defined interfaces (studs)]
- [Self-contained components (bricks)]

## Commit Strategy

Detailed commit plan:

**Commit 1**: [Chunk 1] - [description]

```
feat: Add core interfaces for [feature]

- Add Module1 with interface X
- Add Module2 with interface Y
- Tests passing
```

**Commit 2**: [Chunk 2] - [description]

```
feat: Implement [feature] business logic

- Implement Module1.method()
- Wire up Module2 integration
- All tests passing
```

[... continue for all commits]

## Risk Assessment

**High Risk Changes**:

- [Change that might break things] - [mitigation]

**Dependencies to Watch**:

- [External library] - [version constraints]

**Breaking Changes**:

- [If any] - [how to handle]

## Success Criteria

Code is ready when:

- [ ] All documented behavior implemented
- [ ] All tests passing (make check)
- [ ] User testing works as documented
- [ ] No regressions in existing functionality
- [ ] Code follows philosophy principles
- [ ] Ready for Phase 4 implementation

## Next Steps

✅ Code plan complete and detailed
➡️ Get user approval
➡️ When approved, run: `/ddd:4-code`

````

### 4. Verify Completeness

**Checklist before presenting to user**:

- [ ] Every code file from Phase 1 plan covered?
- [ ] Clear what changes for each file?
- [ ] Implementation broken into chunks?
- [ ] Dependencies between chunks identified?
- [ ] Test strategy defined?
- [ ] Agent orchestration planned?
- [ ] Commit strategy clear?
- [ ] Philosophy alignment verified?

### 5. Present for Approval

Show user:
- The code plan document
- Summary of changes
- Implementation approach
- Estimated scope/chunks

**Get explicit approval before proceeding to Phase 4**

---

## Using TodoWrite

Track code planning tasks:

```markdown
- [ ] Read all updated documentation
- [ ] Reconnaissance of file 1 of N
- [ ] Reconnaissance of file 2 of N
...
- [ ] Implementation spec written
- [ ] Chunks defined
- [ ] Test strategy defined
- [ ] User approval obtained
````

---

## Agent Suggestions

**zen-architect** - For architecture review:

```
Task zen-architect: "Review code plan for architecture compliance
with IMPLEMENTATION_PHILOSOPHY and MODULAR_DESIGN_PHILOSOPHY"
```

**modular-builder** - To validate buildability:

```
Task modular-builder: "Review code plan, assess if specs are complete
enough for implementation"
```

---

## Important Notes

**Documentation is the spec**:

- Code MUST match what docs describe
- If docs are ambiguous, ask user to clarify docs first
- If implementing reveals docs need changes, update docs first

**Right-sizing chunks**:

- Each chunk should fit in context window
- Each chunk should be independently testable
- Each chunk should have clear commit point
- Breaking into too many chunks is better than too few

**DO NOT write code yet**:

- This phase is PLANNING only
- All actual implementation happens in Phase 4
- Get user approval on plan before coding

---

## When Plan is Approved

### Exit Message

```
✅ Phase 3 Complete: Code Plan Approved

Implementation plan written to: ai_working/ddd/code_plan.md

Summary:
- Files to change: [count]
- Implementation chunks: [count]
- New tests: [count]
- Estimated commits: [count]

⚠️ USER APPROVAL REQUIRED

Please review the code plan above.

When approved, proceed to implementation:

    /ddd:4-code

Phase 4 will implement the plan incrementally, with your
authorization required for each commit.
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

**"Current code is very different from docs"**

- That's expected - docs show target state
- Plan the transformation from current → target
- May need multiple chunks to bridge the gap

**"Unsure how to break into chunks"**

- Start with interfaces/data models (others depend on these)
- Then implement business logic
- Then wire up integrations
- Each should be independently testable

**"Implementation seems too complex"**

- Check against ruthless simplicity principle
- Is there a simpler approach?
- Are we future-proofing unnecessarily?
- Consult with user

**"Conflicts between code reality and docs"**

- Docs are the spec (we updated them in Phase 2)
- If docs are wrong, go back and fix docs first
- Don't implement what docs don't describe

---

Need help? Run `/ddd:0-help` for complete guide
