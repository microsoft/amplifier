# Amplifier Profiles System

**Making development methodology itself a first-class, mutable abstraction.**

## What Are Profiles?

Profiles externalize your entire development process and philosophy, making the methodology itself subject to development and refinement. Instead of a one-size-fits-all approach, you can choose (or create) methodologies tailored to your context.

Think of profiles as **cognitive prostheses** — externalizations of how you think about and approach development that can be refined, measured, and evolved over time.

## Quick Start

### View Available Profiles

```bash
/profile list
```

### See Current Profile

```bash
/profile show
```

### Switch Profiles

```bash
/profile use waterfall    # For projects with clear requirements
/profile use profile-meta # For developing new methodologies
/profile use default      # Back to doc-driven minimalism
```

## Available Profiles

### `default/` - Document-Driven Ruthless Minimalism

**Philosophy**: Documentation leads, code follows. Ruthless simplicity. Trust in emergence.

**Best for**:
- Projects with evolving requirements
- Long-term maintainability
- Teams valuing simplicity over cleverness
- When documentation quality matters

**Process**: Iterative DDD workflow with flexible gates

**Key principles**: Wabi-sabi, Occam's razor, modular "bricks & studs"

### `profile-meta/` - Methodology Development

**Philosophy**: The development methodology itself becomes subject to development.

**Best for**:
- Creating new development profiles
- Refining existing methodologies
- Analyzing process effectiveness
- Building composable workflows

**Process**: Meta-cognitive development of processes themselves

**Key principles**: Measure effectiveness, embrace evolution, context matters

### `waterfall/` - Phased Sequential Development

**Philosophy**: Measure twice, cut once. Comprehensive upfront planning.

**Best for**:
- Embedded systems and hardware integration
- Regulated industries (medical, financial, aerospace)
- Fixed-price contracts
- When change is very expensive

**Process**: Six sequential phases with strict gates

**Key principles**: Phase discipline, comprehensive planning, formal change control

## Profile Structure

Every profile contains:

```
profiles/{profile-name}/
├── profile.md          # The "pitch" - overview and philosophy
├── philosophy/         # Deep philosophy documents
│   └── *.md
├── commands/          # Workflow commands
│   └── *.md
└── agents/            # Specialized agents (optional)
    └── *.md
```

### `profile.md` - The Pitch

Quick overview containing:
- **The Pitch**: What this methodology is about
- **Core Philosophy**: Principles and beliefs
- **Process Overview**: How development flows
- **When to Use**: Context where it excels
- **When NOT to Use**: Boundaries and limitations
- **Success Metrics**: How to measure effectiveness

### `philosophy/` - Deep Philosophy

Detailed documents explaining:
- Core principles and their rationale
- Decision-making frameworks
- Trade-offs and constraints
- Historical context

### `commands/` - Workflow Implementation

Executable commands implementing the process:
- Phase-specific workflows
- Process utilities
- Methodology-specific tools

### `agents/` - Specialized Agents

Agents embodying the profile's principles:
- Process-aware automation
- Domain-specific expertise
- Philosophy-aligned decision-making

## Shared Resources

`profiles/shared/` contains resources available to all profiles:

```
profiles/shared/
├── commands/          # Generic commands (commit, review, etc.)
├── agents/           # Domain-agnostic agents (security, performance)
└── tools/            # Shared utilities (hooks, formatters)
```

Profiles can import shared resources using `@shared/commands/commit.md` syntax.

## Composition System

Profiles support compositional architecture:

```markdown
## Composition

This profile imports from:
- `@shared/commands/commit.md` - Version control
- `@shared/agents/security-guardian.md` - Security review
- `@profiles/default/agents/zen-architect.md` - From another profile
```

This enables:
- **Reuse** of common tools across profiles
- **Hybrid** methodologies combining multiple approaches
- **Evolution** by mixing and matching techniques

## Creating Your Own Profile

Use the `profile-meta` profile to create new methodologies:

```bash
# Switch to profile-meta
/profile use profile-meta

# Create a new profile
/create-profile

# Answer questions about:
# - What problem does this methodology solve?
# - What are the core principles?
# - What's the process workflow?
# - When should/shouldn't it be used?
```

The system will scaffold a complete profile structure for you to customize.

## Refining Existing Profiles

Methodologies should evolve based on real-world use:

```bash
# Switch to profile-meta
/profile use profile-meta

# Refine a profile
/refine-profile default

# The system will:
# - Analyze current state
# - Identify friction points
# - Suggest improvements
# - Measure impact
```

## Active Profile System

The active profile is managed via symlink at `.claude/active-profile`:

```bash
# Current active profile
readlink .claude/active-profile
# → ../profiles/default

# Switch profile
ln -sf ../profiles/waterfall .claude/active-profile

# Or use the command
/profile use waterfall
```

Claude Code reads the active profile to determine:
- Available commands
- Available agents
- Process philosophy
- Workflow structure

## Profile Comparison

Compare methodologies to choose the right one:

```bash
/profile compare default waterfall
```

Shows:
- Philosophy differences
- Process approach
- Trade-offs
- When to use each

## Success Metrics

**The profiles system succeeds when:**
- Developers can articulate their process clearly
- Methodologies evolve based on measured results
- New profiles emerge from team needs
- Process improvements compound over time
- Institutional knowledge grows systematically

**Warning signs:**
- Profiles become dogma rather than tools
- No measurement of methodology effectiveness
- Resistance to process evolution
- Profiles divorced from actual practice

## Philosophy

### Why Externalize Methodology?

Traditional development processes are:
- **Implicit**: Exist only in developers' heads
- **Static**: Rarely evolve or improve
- **Tribal**: Passed through osmosis, lost when people leave
- **One-size-fits-all**: Same process for all contexts

Externalized profiles are:
- **Explicit**: Clearly documented and understood
- **Evolvable**: Refined based on results
- **Transferable**: Easily shared and taught
- **Context-aware**: Different profiles for different needs

### The Meta-Cognitive Advantage

By making the development process itself mutable and subject to development, we create a **cognitive prosthesis**:

- **Externalized**: Methodology exists outside your head
- **Measurable**: Effectiveness can be assessed objectively
- **Improvable**: Process can evolve based on data
- **Composable**: Techniques can be mixed and matched
- **Teachable**: New developers learn explicit process

This elevates Amplifier from a toolkit to a system for developing better ways to develop.

## Future Directions

Potential additions:
- **mathematical-elegance/** - Pure functional, type-driven development
- **experimental/** - For research and exploration
- **pair/** - Collaborative human-AI development
- **teaching/** - For explaining concepts and mentoring
- **security-first/** - For high-assurance systems

Create your own profiles to match your needs!

---

**Further Reading:**
- `default/profile.md` - Doc-driven minimalism details
- `profile-meta/profile.md` - Meta-development details
- `waterfall/profile.md` - Phased development details
- `profile-meta/philosophy/profile-development.md` - Deep philosophy on methodology development

---

_"The methodology that cannot adapt is already obsolete. Make your process as evolvable as your code."_
