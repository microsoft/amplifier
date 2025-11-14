# PRD Writing Guide for AI-First Development

## Core Philosophy

**PRDs are not implementation contracts. They are research-based intentions with flexibility built in.**

The fundamental problem with traditional PRDs in AI-assisted development:
- **Too strict** → Trying to force reality into predictions ("натягивание совы на глобус")
- **Too flexible** → Lost context from preliminary research, AI makes random choices

**The balance**: Write PRDs that capture WHAT and WHY, suggest probable HOW based on research, but explicitly allow evolution during implementation.

## The Fundamental Challenge

### The Reality of PRD Creation

```
Session 1: User + AI write PRD
- Conduct preliminary research
- Document findings
- Make assumptions about implementation
- User approves PRD

Session 2: Different AI instance reads PRD
- No context about how PRD was generated
- Sees approved document as "truth"
- Doesn't know what user was thinking
- Can't predict actual implementation challenges
```

### The Problem This Creates

**PRD becomes a contract instead of a guide:**
- Trade-offs appear during implementation
- Better approaches are discovered
- Original assumptions prove wrong
- But AI tries to implement "for the sake of PRD" instead of "for the sake of working solution"

**This is bad. We need flexibility.**

But too much flexibility loses the value of preliminary research and context.

## The Solution: Flexible, Research-Informed PRDs

### What to Include in PRD

#### 1. User Intent (Required)
**WHAT the user wants:**
```markdown
## User Intent
[Clear statement of what the user wants to achieve]
[Specific requirements or constraints]
```

**WHY this matters:**
```markdown
## Why This Feature
[Business or user value]
[Problem being solved]
```

**Clear, unambiguous, doesn't change.**

#### 2. Preliminary Research (Informational)
**Research findings IN GENERAL TERMS:**
```markdown
## Preliminary Research

**Observation**: Reference implementation has working [feature area]
- File `module-x.js` PROBABLY handles [specific functionality]
- File `ComponentY.js` LIKELY manages [specific aspect]
- [Pattern/communication] SEEMS TO coordinate between [components]

**Note**: These are initial observations. VERIFY during implementation.
```

**Key words**: "probably", "likely", "seems to", "appears to"

#### 3. Suggested Approach (Non-Binding)
**General direction, not specific steps:**
```markdown
## Suggested Approach

**Overall strategy**: Leverage existing reference code where possible

**Key areas to explore**:
- [Area 1] (reference shows [approach])
- [Area 2] (reference uses [pattern])
- [Area 3] (reference has this solved)

**Recommendation**: Study reference patterns before implementing from scratch.

⚠️ **This is a suggestion based on preliminary research.**
**If better approaches are discovered during implementation, use them.**
```

#### 4. Explicit Flexibility Clause (Required)
```markdown
## Implementation Flexibility

**This PRD is based on preliminary research and assumptions.**

During implementation:
- ✅ Conduct additional research as needed
- ✅ Verify assumptions before proceeding
- ✅ Adapt approach if better solutions are discovered
- ✅ Ask user for guidance when trade-offs appear
- ❌ DO NOT blindly follow PRD if reality differs
- ❌ DO NOT force implementation to match PRD

**If something doesn't work as described:**
1. Stop and investigate why
2. Conduct new research
3. Propose alternative approach
4. Get user confirmation
5. Continue with better solution
```

#### 5. Phase Separation (Required)
```markdown
## Phase 1: Functional Implementation

**Goal**: Make it work

**In Scope**:
- Core functionality working end-to-end
- User can verify it works correctly

**Out of Scope**:
- Linting (saves context for functionality research)
- Comprehensive tests (saves context for architecture decisions)
- Perfect code style (saves context for problem-solving)

**Why**: Complex features need context budget for:
- Research and exploration
- Architectural thinking
- Problem-solving and debugging
- Trade-off evaluation

Linting and testing are important but consume context that's better spent on getting functionality right first.

**Acceptance Criteria**:
- [ ] User tests functionality manually
- [ ] User confirms: "It works"
- [ ] Core requirements met

## Phase 2: Quality and Integration (Future)

**Goal**: Polish and integrate

**In Scope**:
- Run linters and fix issues
- Add comprehensive tests
- Optimize and refactor
- Documentation

**Trigger**: After user confirms Phase 1 works
```

### What NOT to Include in PRD

#### ❌ Specific Implementation Steps
```markdown
BAD:
Step 1: Copy file X to directory Y
Step 2: Create function Z in file A
Step 3: Import module B from path C

GOOD:
Consider leveraging reference implementation's [feature] logic.
Files to study: [list of relevant files]
```

#### ❌ Strict File Paths and Structure
```markdown
BAD:
Create src/utils/feature/module.ts
Create src/components/Feature/Component.tsx

GOOD:
Suggested structure:
- Utility layer for [functionality]
- Component layer for [UI/logic]
Exact organization can be determined during implementation.
```

#### ❌ Definitive "Must Use This Approach"
```markdown
BAD:
MUST use [specific technology/pattern]
MUST use [specific implementation detail]

GOOD:
Reference implementation uses [technology/pattern] for [purpose].
[Pattern] appears to coordinate between [components].
Verify this approach works for our use case.
```

#### ❌ Assumptions Presented as Facts
```markdown
BAD:
The module-x.js file handles all cases perfectly.

GOOD:
The module-x.js file appears to handle [functionality].
Verify it works for our specific requirements during implementation.
```

## Writing Process

### 1. Research Phase
- Study existing code (reference, current implementation)
- Identify patterns and potential solutions
- Document observations and uncertainties
- Note what seems important vs what's unclear

### 2. Documentation Phase
**Document in order of certainty:**

**High Certainty** (User Intent):
```markdown
## Requirements
- User wants [clear feature description]
- Must [specific constraint or requirement]
```

**Medium Certainty** (Research Findings):
```markdown
## Research Findings
Reference implementation APPEARS to solve similar problem.
Key files to study: [list]
Potential approach: [general description]
```

**Low Certainty** (Suggestions):
```markdown
## Suggested Exploration Areas
- [Approach 1] (reference uses this approach)
- [Approach 2] (reference has implementations)
VERIFY these approaches during implementation.
```

### 3. Flexibility Phase
Add explicit guidance:
```markdown
## How to Use This PRD

**This document provides direction, not rigid instructions.**

When implementing:
1. Start with user requirements (high certainty)
2. Verify research findings (medium certainty)
3. Evaluate suggestions (low certainty)
4. Adapt based on what you discover

**Remember**: The goal is working software that meets user needs,
not perfect adherence to preliminary assumptions.
```

## Common Pitfalls and Solutions

### Pitfall 1: PRD Too Strict
**Problem**: AI treats PRD as unbreakable contract, forces wrong solution

**Solution**: Add flexibility clauses, use uncertain language ("probably", "seems"), explicitly allow adaptation

### Pitfall 2: PRD Too Vague
**Problem**: AI has no direction, makes random architectural choices

**Solution**: Include research findings and suggested approaches, but mark them as preliminary

### Pitfall 3: Lost Context from Research
**Problem**: Next session AI doesn't know why certain decisions were made

**Solution**: Document reasoning: "We chose X because Y, but if Z is true, consider alternative"

### Pitfall 4: Implementation Gets Stuck
**Problem**: Reality differs from PRD assumptions, AI doesn't know what to do

**Solution**: Explicit instruction: "If stuck, conduct new research. Don't force PRD approach."

### Pitfall 5: Context Budget Exhausted
**Problem**: Trying to do functionality + linting + tests + perfect code in one session

**Solution**: Phase 1 (functionality only), Phase 2 (quality). Saves context for what matters.

## Phase 1 Context Budget Strategy

### Why Defer Linting and Testing

**Context is a limited resource.** Complex features need it for:
- Understanding existing code
- Researching approaches
- Thinking through architecture
- Solving implementation challenges
- Evaluating trade-offs

**Linting consumes context with:**
- Style issues that don't affect functionality
- Import organization
- Formatting discussions
- Type perfection

**Testing consumes context with:**
- Test infrastructure setup
- Mock creation
- Edge case enumeration
- Test debugging

**Both are important, but not during initial implementation.**

### What Phase 1 Focuses On

**Use context budget for:**
- Research and exploration ("How does reference solve this?")
- Architectural decisions ("Should we use pattern X or Y?")
- Problem-solving ("Component X isn't integrating correctly with Y")
- Trade-off evaluation ("Performance vs code clarity here")
- Integration challenges ("Communication between modules not working properly")

**These are harder to fix later** because they affect core design.

Lint issues and missing tests are **easier to fix later** because they don't change functionality.

### Phase 1 Success Criteria

```markdown
**Phase 1 Complete When:**
- [ ] Feature works end-to-end
- [ ] User manually tests: "Yes, it works"
- [ ] Core requirements met
- [ ] No critical bugs

**NOT Required:**
- Zero lint errors (Phase 2)
- Comprehensive tests (Phase 2)
- Perfect code style (Phase 2)
- Complete documentation (Phase 2)
```

### Transitioning to Phase 2

**After user confirms Phase 1:**
```markdown
User: "It works correctly"

Now safe to spend context on:
- Running linters and fixing issues incrementally
- Writing comprehensive test coverage
- Refactoring for better structure
- Optimizing performance
- Adding documentation
```

**Why this works:**
- Functionality is proven working
- Architecture is validated
- Context is freed up from research/problem-solving
- Can focus entirely on quality improvements

## Example PRD Structure

### ❌ Bad PRD (Too Strict)
```markdown
# Feature Implementation

## Steps
1. Copy module-x.js to src/utils/feature/
2. Create ComponentY.tsx in src/components/Feature/
3. Add handler 'feature:action' in main.ts line 150
4. Import utility in TriggerComponent.tsx
5. Call API method on user action

## Requirements
- MUST use the module-x.js file
- MUST create component with specific configuration
- MUST use specific pattern for communication
```

**Problems:**
- Specific implementation steps (what if better approach exists?)
- Absolute requirements ("MUST") leave no room for adaptation
- No flexibility if assumptions are wrong
- Next session AI will force this even if it doesn't work

### ✅ Good PRD (Flexible, Research-Informed)

```markdown
# PRD: [Feature Name]

## User Intent
[Clear statement of what user wants to achieve]
[Specific requirements or constraints]

## Why This Matters
[Business or user value]
[Problem being solved]

## Preliminary Research

**Reference Implementation Analysis:**
- File `module-x.js` APPEARS to handle [functionality]
  - Observation: [What you observed]
  - Uncertainty: Need to verify [specific aspect]
- File `ComponentY.js` SEEMS to manage [aspect]
  - Observation: [What you observed]
  - Uncertainty: Need to verify [specific aspect]
- [Pattern] APPEARS to coordinate [components]
  - Observation: [What you observed]
  - Uncertainty: Need to verify [specific aspect]

**These are preliminary observations. VERIFY during implementation.**

## Suggested Approach

**General Strategy**: Study and potentially leverage reference implementation

**Key Areas to Explore:**
1. **[Area 1]**: Reference uses [approach]
   - Verify this approach works for our use case
   - Consider alternatives if issues arise
2. **[Area 2]**: Reference has [pattern]
   - Evaluate if we can reuse this logic
   - Research alternatives if needed
3. **[Area 3]**: Reference appears to handle this
   - Study [specific aspect] approach
   - Verify it works with our requirements

**This is a starting point, not a prescription.**

## Implementation Flexibility

⚠️ **Important**: This PRD is based on preliminary research.

**During implementation:**
- Verify all assumptions before proceeding
- If reference approach doesn't work, explore alternatives
- If better patterns are discovered, use them
- If stuck, conduct additional research
- Prioritize working solution over PRD adherence

**If something doesn't work:**
1. Stop and analyze why
2. Research alternative approaches
3. Propose new direction
4. Get user confirmation
5. Continue with better solution

## Phase 1: Functional Implementation

**Goal**: Make [feature] work

**In Scope:**
- [Core functionality working end-to-end]
- [User can verify it works correctly]
- [Core requirements met]

**Out of Scope (Phase 1):**
- Linting and code style
- Comprehensive test coverage
- Perfect type integration
- Performance optimization

**Why**: Save context budget for:
- Research and architecture decisions
- Problem-solving during implementation
- Trade-off evaluation
- Integration challenges

**Acceptance Criteria:**
- [ ] [Specific testable outcome]
- [ ] [Specific testable outcome]
- [ ] User confirms: "It works correctly"

## Phase 2: Quality (After Phase 1 Approval)

**In Scope:**
- Run linters, fix issues
- Add comprehensive tests
- Optimize and refactor
- Documentation

**Trigger**: User confirms Phase 1 works
```

**Why This Works:**
- Clear user intent (unchangeable)
- Research findings marked as preliminary
- Flexible approach with alternatives allowed
- Explicit permission to adapt
- Phase separation preserves context budget
- Focus on working solution first, quality second

## Summary: PRD Writing Checklist

### ✅ Must Include
- [ ] Clear user intent (WHAT and WHY)
- [ ] Preliminary research findings (marked as such)
- [ ] Suggested approach (non-binding)
- [ ] Explicit flexibility clause
- [ ] Phase 1 (functionality) vs Phase 2 (quality) separation
- [ ] Acceptance criteria for each phase
- [ ] Instruction to verify assumptions during implementation

### ❌ Must NOT Include
- [ ] Specific implementation steps ("Step 1: Do X")
- [ ] Rigid file paths and structure
- [ ] Absolute requirements without alternatives ("MUST use X")
- [ ] Assumptions presented as facts
- [ ] Linting/testing requirements in Phase 1
- [ ] Everything-at-once approach

### 🎯 Goal
**PRD should guide without constraining.**

Capture WHAT user wants and WHY.
Suggest HOW based on research.
Allow evolution as reality emerges.
Preserve context for what matters.

**Remember**: The goal is working software that meets user needs, not perfect adherence to preliminary assumptions.