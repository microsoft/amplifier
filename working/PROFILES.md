# Amplifier Profiles System

**Elevating methodology itself to a first-class, mutable abstraction.**

## The Vision

Amplifier claimed to be a "metacognitive toolkit" but remained prescriptive about *how* development should happen. The profiles system completes the vision: **the development methodology itself becomes externalized, mutable, and subject to development.**

This isn't just about having different workflows — it's about making the entire development process a cognitive prosthesis that can be analyzed, measured, refined, and evolved.

## What Are Profiles?

Profiles are complete development methodologies externalized as:
- **Philosophy** - Core principles and decision-making frameworks
- **Process** - Workflow steps, phase gates, feedback loops
- **Tools** - Commands and agents that embody the methodology
- **Documentation** - When to use, success metrics, trade-offs

Think of profiles as **ideological frameworks for development** that can be:
- Chosen based on context
- Measured for effectiveness
- Refined through use
- Composed from reusable parts
- Shared between teams

## Why This Matters

### The Problem with Implicit Methodology

Most development happens with implicit, undocumented processes:
- "How we do things around here" lives only in people's heads
- New team members learn by trial and error
- Process improvements are ad-hoc and forgotten
- One methodology applied to all contexts
- No measurement of methodology effectiveness

### The Profiles Solution

Externalized methodologies enable:

**Explicit Process**: Document philosophy, principles, and workflow clearly

**Context-Appropriate**: Different profiles for different project needs
- Evolving requirements? → `default` profile
- Fixed requirements, expensive changes? → `waterfall` profile
- Developing new processes? → `profile-meta` profile

**Measurable**: Track methodology effectiveness objectively
- Time to working feature
- Defect rates
- Developer satisfaction
- Maintainability metrics

**Evolvable**: Refine profiles based on real-world results
- Identify friction points
- Test improvements
- Measure impact
- Compound learnings

**Composable**: Mix and match techniques from different methodologies
- Shared commands/agents across profiles
- Cross-profile references
- Hybrid approaches

## Available Profiles

### `default/` - Document-Driven Ruthless Minimalism

The original Amplifier methodology elevated to profile status.

**Philosophy**: Documentation leads, code follows. Ruthless simplicity. Trust in emergence.

**Process**: Iterative DDD workflow (plan → docs → code-plan → code → finish)

**Best for**:
- Projects with evolving requirements
- Long-term maintainability
- When documentation quality matters
- Teams valuing simplicity

**Key Principles**:
- Wabi-sabi philosophy (embrace simplicity)
- Occam's Razor (simplest solution)
- Modular "bricks & studs" architecture
- Human architects, AI builds

---

### `profile-meta/` - Methodology Development

The meta-cognitive layer: developing how we develop.

**Philosophy**: The development methodology itself becomes subject to development.

**Process**: Create → Test → Refine → Measure → Evolve

**Best for**:
- Creating new development profiles
- Refining existing methodologies
- Analyzing process effectiveness
- Building composable workflows

**Key Principles**:
- Question assumptions
- Measure effectiveness
- Embrace evolution
- Context matters

---

### `waterfall/` - Phased Sequential Development

Traditional methodology adapted for AI-assisted development.

**Philosophy**: Measure twice, cut once. Comprehensive upfront planning.

**Process**: Six sequential phases with strict gates
1. Requirements Gathering
2. System Design
3. Detailed Design
4. Implementation
5. Integration & Testing
6. Deployment & Maintenance

**Best for**:
- Embedded systems and hardware integration
- Regulated industries (medical, financial, aerospace)
- Fixed-price contracts
- When change is very expensive

**Key Principles**:
- Phase discipline (no skipping)
- Comprehensive planning
- Formal change control
- Traceability and audit trail

---

## Quick Start

### View Available Profiles

```bash
/profile list
```

### See What Profile You're Using

```bash
/profile show
```

### Switch Profiles

```bash
/profile use waterfall    # For hardware/regulatory projects
/profile use profile-meta # To develop new methodologies
/profile use default      # Back to doc-driven minimalism
```

### Compare Methodologies

```bash
/profile compare default waterfall
```

## Creating Your Own Profile

The system is designed for you to create methodologies tailored to your needs:

```bash
# Switch to meta-development profile
/profile use profile-meta

# Create a new profile
/create-profile

# Answer questions about:
# - What problem does this methodology solve?
# - What are core principles?
# - What's the process workflow?
# - When should/shouldn't it be used?
```

Example custom profiles you might create:
- **mathematical-elegance/** - Type-driven, proof-based development
- **experimental/** - For research and exploration
- **security-first/** - For high-assurance systems
- **teaching/** - For explaining concepts and mentoring
- **startup-mvp/** - For rapid prototyping and validation

## How It Works

### Profile Structure

```
profiles/
├── {profile-name}/
│   ├── profile.md      # The "pitch" - quick overview
│   ├── philosophy/     # Deep philosophy docs
│   │   └── *.md
│   ├── commands/       # Workflow commands
│   │   └── *.md
│   └── agents/         # Specialized agents (optional)
│       └── *.md
│
└── shared/             # Resources shared across profiles
    ├── commands/       # Generic commands
    ├── agents/        # Domain-agnostic agents
    └── tools/         # Shared utilities
```

### Active Profile

The current profile is tracked via symlink:

```bash
.claude/active-profile -> ../profiles/default
```

Claude Code reads the active profile to determine available commands, agents, and process philosophy.

### Composition

Profiles can import shared resources:

```markdown
@shared/commands/commit.md          # Shared command
@shared/agents/security-guardian.md  # Shared agent
@profiles/default/agents/zen-architect.md  # From another profile
```

This enables:
- Reuse of common tools
- Hybrid methodologies
- Learning from other approaches

## The Meta-Cognitive Advantage

By making methodology itself mutable and subject to development, Amplifier becomes a true **cognitive prosthesis**:

**Externalized**: Process exists outside your head, explicitly documented

**Measurable**: Effectiveness assessed objectively with metrics

**Improvable**: Methodology evolves based on real-world results

**Composable**: Techniques mixed and matched across profiles

**Teachable**: New developers learn explicit, documented process

**Evolvable**: Process improves as code does

This completes the Amplifier vision: **not just a toolkit for externalizing development work, but a toolkit for externalizing the entire development process and philosophy.**

## Philosophy

### Methodologies Are Tools, Not Dogma

There is no "best" development methodology. The right approach depends on context:
- Team size and experience
- Project complexity and risk
- Requirements stability
- Timeline and budget
- Regulatory constraints
- Technical constraints

Profiles make methodology selection explicit and context-aware.

### Process Should Be As Evolvable As Code

We iterate on code. We should iterate on process.

Profiles enable:
- Measuring methodology effectiveness
- Identifying process friction
- Testing improvements
- Adopting what works
- Discarding what doesn't

### Meta-Cognitive Development

The highest leverage comes from improving how you improve:
- Better code → Better features
- Better process → Better code AND better features
- Better meta-process → Better processes → Better code → Better features

Profiles enable meta-cognitive development: making the process itself subject to the process.

## Success Metrics

**The profiles system succeeds when:**
- Methodologies emerge from team needs, not imposed from above
- Profiles evolve based on measured results
- Developers articulate their process clearly
- Process improvements compound over time
- Institutional knowledge grows systematically
- Teams choose context-appropriate methodologies

**Warning signs:**
- Profiles become dogma rather than tools
- No measurement of methodology effectiveness
- Resistance to process evolution
- Profiles divorced from actual practice
- One methodology applied to all contexts

## Future Directions

### Additional Profiles

The system is designed to grow:
- **tdd/** - Test-driven development
- **bdd/** - Behavior-driven development
- **exploratory/** - Research and prototyping
- **lean/** - Validated learning cycles
- **chaos-engineering/** - Resilience-first development
- **performance-first/** - Optimization-driven development

### Profile Composition

Future enhancements:
- Profiles as DAGs (directed acyclic graphs) of inherited traits
- Dynamic profile switching within a project
- Profile metrics and analytics
- Profile marketplace and sharing
- AI-generated profile recommendations based on project characteristics

### Organizational Learning

Profiles enable:
- Team-specific methodologies
- Cross-team process sharing
- Systematic capture of "how we work"
- Onboarding through explicit process
- Process evolution tracking

## Getting Started

1. **Understand current profile**: `/profile show`
2. **Explore alternatives**: `/profile list` and `/profile compare`
3. **Try a different approach**: `/profile use waterfall` (or profile-meta)
4. **Create your own**: `/profile use profile-meta` then `/create-profile`
5. **Measure and refine**: Track metrics, identify friction, improve

## Further Reading

- `profiles/README.md` - Complete profiles documentation
- `profiles/default/profile.md` - Default methodology details
- `profiles/profile-meta/profile.md` - Meta-development guide
- `profiles/waterfall/profile.md` - Waterfall methodology details
- `.claude/README_PROFILES.md` - Technical implementation details

---

**From the Amplifier Vision:**

> _"We're not building another dev tool. We're changing the fundamental equation of human capability."_

The profiles system completes this vision. Not just a tool for building software, but **a toolkit for externalizing, refining, and evolving how we build software itself.**

---

_"The methodology that cannot adapt is already obsolete. Make your process as evolvable as your code."_
