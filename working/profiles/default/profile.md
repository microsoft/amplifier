# Default Profile: Document-Driven Ruthless Minimalism

## The Pitch

**Development as a meditative practice: Build only what's needed, exactly when it's needed.**

This profile embodies a zen approach to software development where documentation leads, code follows, and simplicity reigns supreme. Every line of code must justify its existence. Every abstraction must prove its value. The philosophy is Wabi-sabi applied to software: embrace imperfection, trust in emergence, and find beauty in minimalism.

## Core Philosophy

**Documentation IS the specification. Code implements what documentation describes.**

We write as if the feature already exists ("retcon writing"), then build exactly what we described. This prevents context poisoning, eliminates doc drift, and ensures human judgment guides architecture before expensive implementation begins.

**Ruthless Simplicity**: Code you don't write has no bugs. Start minimal, grow as needed, question everything.

**Modular "Bricks & Studs"**: Build regeneratable modules under 150 lines with clear contracts. Don't patch — regenerate from specs.

**Human Architects, AI Builds**: Humans provide vision and review. AI handles exploration and implementation.

## Process Overview

### The DDD Workflow

1. **Plan** (`/ddd:1-plan`) - Design the feature, understand requirements
2. **Document** (`/ddd:2-docs`) - Update all non-code files (iterate until approved)
3. **Code Plan** (`/ddd:3-code-plan`) - Plan code changes with specifications
4. **Implement** (`/ddd:4-code`) - Build and verify (iterate until working)
5. **Finish** (`/ddd:5-finish`) - Clean up and finalize

Each phase creates artifacts the next phase consumes. Approval gates prevent rushing ahead. You control all git operations.

### Key Techniques

- **File Crawling**: Process many files systematically (99.5% token reduction)
- **Retcon Writing**: Write as if feature already exists (no "will be")
- **Context Poisoning Prevention**: Maximum DRY, eliminate conflicts
- **Progressive Organization**: Right-sized docs (README → Overview → Details)
- **Vertical Slices**: Complete end-to-end functionality first

## When to Use This Profile

**Perfect for:**
- Features requiring careful architectural thought
- Projects where documentation quality matters
- Teams that value maintainability over speed
- Codebases that will live for years
- When you want to prevent technical debt

**Not ideal for:**
- Rapid prototyping and experimentation
- Throwaway proof-of-concepts
- When process overhead exceeds project complexity
- Pure research or exploration tasks

## Key Principles

### Design Decisions

For EVERY decision, ask:
1. **Necessity**: "Do we actually need this right now?"
2. **Simplicity**: "What's the simplest way to solve this?"
3. **Directness**: "Can we solve this more directly?"
4. **Value**: "Does complexity add proportional value?"
5. **Maintenance**: "How easy to understand and change?"

### Areas to Design Carefully

- Security (design robust security from start)
- Data integrity (plan consistency guarantees)
- Core UX (design primary flows thoughtfully)
- Error handling (plan clear error strategies)

### Areas to Keep Simple

- Internal abstractions (minimal layers)
- Generic solutions (design for current needs)
- Edge cases (focus on common cases)
- State management (explicit state flow)

## Success Metrics

**Good code results in:**
- Junior developer can understand it
- Fewer files and folders
- Less documentation needed
- Faster tests
- Easier debugging
- Quicker onboarding

**Warning signs:**
- Fighting abstractions
- Excessive workarounds
- Documentation contradicts code
- Unclear module boundaries

## Philosophy Foundation

This profile builds on two core documents:
- `@philosophy/implementation.md` - Ruthless simplicity principles
- `@philosophy/design.md` - Modular "bricks & studs" architecture

## Available Tools

**Commands**: `/ddd:*` workflow, `/ultrathink-task`, `/designer`, `/commit`, `/review-changes`

**Agents**: `zen-architect`, `modular-builder`, `bug-hunter`, `security-guardian`, and 20+ specialized agents

## Composition

This profile can import from:
- `@shared/commands/*` - Generic cross-profile commands
- `@shared/agents/*` - Reusable specialized agents
- `@shared/tools/*` - Shared utilities

---

_"The best design is often the simplest. Great architecture enables simple implementation."_
