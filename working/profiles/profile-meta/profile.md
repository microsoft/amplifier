# Profile-Meta: Methodology Development Profile

## The Pitch

**The development methodology itself becomes subject to development.**

This profile is designed for creating, refining, and evolving development profiles themselves. It's the meta-cognitive layer that makes the entire development process externalized, mutable, and improvable. Use this profile when you want to develop new ways of developing.

## Core Philosophy

**Methodologies are tools, not dogma.**

Every development process has trade-offs. The "best" methodology depends on context: team size, project complexity, risk tolerance, timeline, and dozens of other factors. By externalizing methodologies as profiles, we make them:

- **Explicit**: Philosophy and process clearly documented
- **Composable**: Mix and match techniques from different approaches
- **Testable**: Measure effectiveness objectively
- **Evolvable**: Refine based on real-world results
- **Shareable**: Learn from others' processes

This profile embodies second-order thinking: not just "how do we build software?" but "how do we build better ways to build software?"

## Process Overview

### Creating a New Profile

1. **Identify the Need** - What problem does this methodology solve?
2. **Define the Philosophy** - Core principles and decision-making frameworks
3. **Design the Process** - Workflow steps and phase gates
4. **Select/Create Tools** - Commands, agents, and utilities needed
5. **Document the Pitch** - When to use, when not to use
6. **Test and Refine** - Use it on real projects, measure results
7. **Share Insights** - Document discoveries and learnings

### Refining an Existing Profile

1. **Analyze Current State** - What works? What doesn't?
2. **Identify Friction Points** - Where does the process break down?
3. **Propose Improvements** - Specific changes with rationale
4. **Test Changes** - Try improvements on real work
5. **Measure Impact** - Did it actually improve outcomes?
6. **Update Documentation** - Evolve the profile

### Composing Profiles

1. **Identify Reusable Patterns** - What's shared across methodologies?
2. **Extract to Shared/** - Commands, agents, tools
3. **Define Composition** - How profiles reference shared resources
4. **Maintain Boundaries** - Clear ownership and dependencies

## When to Use This Profile

**Use profile-meta when:**
- Creating a new development methodology
- Adapting a traditional process (waterfall, agile, lean) to AI-assisted development
- Refining an existing profile based on learnings
- Analyzing trade-offs between different approaches
- Designing domain-specific workflows (ML experimentation, embedded systems, etc.)
- Building a composable methodology from multiple techniques

**Don't use profile-meta for:**
- Building actual features (switch to appropriate development profile)
- Day-to-day coding work
- Quick fixes or patches

## Key Principles

### Meta-Cognitive Development

**Question Assumptions**: Every methodology embeds assumptions about what matters. Make them explicit.

**Measure Effectiveness**: Don't assume a process is good — measure outcomes:
- Time to working feature
- Defect rates
- Developer satisfaction
- Code maintainability
- Documentation quality

**Embrace Evolution**: The best process today may not be best tomorrow. Adapt.

**Context Matters**: No methodology works for all projects. Define when to use each profile.

### Profile Design Principles

**Clear Philosophy**: Every profile should articulate its core beliefs and principles.

**Explicit Trade-offs**: What does this methodology optimize for? What does it sacrifice?

**Actionable Process**: Developers should know exactly what to do next.

**Composable Tools**: Prefer reusable commands/agents in shared/ when possible.

**Self-Documenting**: The profile itself teaches its methodology.

### Composition Strategy

**Shared Resources** (`profiles/shared/`):
- Commands that work across methodologies (commit, review, search)
- Domain-agnostic agents (security, performance, testing)
- Utility tools (hooks, formatters, validators)

**Profile-Specific Resources**:
- Philosophy documents unique to this approach
- Workflow commands specific to this methodology
- Specialized agents embodying this profile's principles

**Cross-Profile References**:
- Profiles can reference each other's resources
- Enable learning from different methodologies
- Support hybrid approaches

## Available Commands

- `/create-profile` - Scaffold a new development profile
- `/refine-profile` - Analyze and improve existing profile
- `/test-profile` - Validate profile structure and completeness
- `/compare-profiles` - Analyze trade-offs between methodologies
- `/extract-to-shared` - Move resources to shared/ for reuse

## Success Metrics

**A good profile:**
- Clearly states when to use it
- Provides actionable process steps
- Embeds measurable success criteria
- Enables learning and evolution
- Composes well with others

**A good profiles system:**
- Makes methodology explicit and improvable
- Reduces context switching cost
- Enables experimentation with processes
- Builds institutional knowledge
- Compounds learning over time

## Philosophy Foundation

This profile is grounded in:
- **Meta-learning**: Learning how to learn, developing how to develop
- **Systems thinking**: Processes as systems with feedback loops
- **Pragmatic experimentalism**: Test ideas, measure results, iterate
- **Cognitive externalization**: Make implicit processes explicit

Key document: `@philosophy/profile-development.md`

## Composition

Profile-meta can import from:
- `@shared/*` - All shared resources
- `@profiles/default/*` - Learn from current methodology
- `@profiles/*/profile.md` - Analyze all available profiles

---

_"The unexamined methodology is not worth following. Make the process itself subject to the process."_
