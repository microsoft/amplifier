---
description: DDD Phase 1 - Planning and design (project:ddd)
argument-hint: [feature description or leave empty to use existing plan]
allowed-tools: TodoWrite, Read, Grep, Glob, Task
---

# DDD Phase 1: Planning & Design

Loading context:

@docs/document_driven_development/overview.md
@docs/document_driven_development/phases/00_planning_and_alignment.md
@docs/document_driven_development/core_concepts/context_poisoning.md
@ai_context/IMPLEMENTATION_PHILOSOPHY.md
@ai_context/MODULAR_DESIGN_PHILOSOPHY.md

Feature: $ARGUMENTS

---

## Your Task: Create Complete Implementation Plan

**Goal**: Design and plan the feature before touching ANY files

**Output**: `ai_working/ddd/plan.md` - Complete specification for all subsequent phases

---

## Phase 1 Steps

### 1. Problem Framing

Answer these questions:

- What are we building?
- Why does it matter?
- What's the user value?
- What problem does this solve?

### 2. Reconnaissance

Explore the codebase:

- Use Glob to find relevant files
- Use Grep to search for related code
- Understand current architecture
- Identify patterns to follow
- Find files that will be affected

**Document**: Current state, related code, architecture context

### 3. Design Proposals

Develop the approach:

- Propose initial design
- Consider alternatives (at least 2)
- Analyze trade-offs
- Check against philosophy:
  - Ruthless Simplicity? ✓
  - Modular Design? ✓
  - Clear interfaces? ✓
- Iterate with user on decisions

**Get user feedback on design direction before proceeding**

### 4. Create Detailed Plan

Write `ai_working/ddd/plan.md` with this structure:

```markdown
# DDD Plan: [Feature Name]

## Problem Statement

[What we're solving and why - clear user value]

## Proposed Solution

[How we'll solve it - high level approach]

## Alternatives Considered

[Other approaches we evaluated and why we chose this one]

## Architecture & Design

### Key Interfaces

[Define the "studs" - how modules connect]

### Module Boundaries

[What goes where, clear separation of concerns]

### Data Models

[Key data structures, if applicable]

## Files to Change

### Non-Code Files (Phase 2)

- [ ] docs/file1.md - [what needs updating]
- [ ] README.md - [what needs updating]
- [ ] config/example.toml - [what needs updating]
      [... complete list of ALL non-code files]

### Code Files (Phase 4)

- [ ] src/module1.py - [what needs changing]
- [ ] src/module2.py - [what needs changing]
      [... complete list of ALL code files]

## Philosophy Alignment

### Ruthless Simplicity

- Start minimal: [how]
- Avoid future-proofing: [what we're NOT building]
- Clear over clever: [examples]

### Modular Design

- Bricks (modules): [list self-contained pieces]
- Studs (interfaces): [list connection points]
- Regeneratable: [could rebuild from this spec]

## Test Strategy

### Unit Tests

[What unit tests we'll need]

### Integration Tests

[What integration tests we'll need]

### User Testing

[How we'll actually test as a user]

## Implementation Approach

### Phase 2 (Docs)

[Specific docs to update, what to document]

### Phase 4 (Code)

[Chunks to implement, order matters if dependencies]

## Success Criteria

[How do we know it's done and working?]

## Next Steps

✅ Plan complete and approved
➡️ Ready for `/ddd:2-docs`
```

---

## Using TodoWrite

Track planning tasks:

```markdown
- [ ] Problem framing complete
- [ ] Reconnaissance done
- [ ] Design proposals drafted
- [ ] User feedback incorporated
- [ ] Detailed plan written
- [ ] Philosophy alignment checked
- [ ] Plan reviewed with user
```

---

## Agent Suggestions

Consider spawning agents for help:

**zen-architect** - For complex architectural decisions:

```
Task zen-architect: "Design approach for [feature], considering
IMPLEMENTATION_PHILOSOPHY and MODULAR_DESIGN_PHILOSOPHY"
```

**Explore agent** - For codebase reconnaissance:

```
Task Explore: "Find all code related to [topic], understand
current patterns and architecture"
```

---

## Important Notes

**DO NOT write any files yet** - This phase is PLANNING ONLY

**Iterate until solid**:

- Get user feedback on design direction
- Refine proposals based on feedback
- Clarify ambiguities
- Ensure shared understanding

**Philosophy check**:

- Does this follow ruthless simplicity?
- Are module boundaries clear?
- Can we build in increments?
- Is this the simplest approach that works?

---

## When Planning is Approved

### Checklist

- [ ] Problem clearly framed
- [ ] Reconnaissance complete
- [ ] Design approach agreed upon
- [ ] All files to change identified
- [ ] Philosophy principles followed
- [ ] Test strategy defined
- [ ] User has reviewed and approved plan

### Exit Message

```
✅ Phase 1 Complete: Planning Approved

Plan written to: ai_working/ddd/plan.md

Next Phase: Update all non-code files (docs, configs, READMEs)

Run: /ddd:2-docs

The plan will guide all subsequent phases. All commands can now
run without arguments using the plan as their guide.
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

**"I don't know where to start"**

- Start with problem framing
- Then do reconnaissance to understand current state
- Design emerges from understanding problem + current state

**"Too many files affected"**

- That's okay - we'll process them systematically in phase 2
- File crawling technique handles large batches

**"Unclear about design direction"**

- Propose 2-3 alternatives
- Present to user with trade-offs
- Iterate until clear

**"Philosophy conflict"**

- If design violates simplicity/modularity, reconsider
- Simpler is usually better
- Ask user if complexity is justified

---

Need help? Run `/ddd:0-help` for complete guide
