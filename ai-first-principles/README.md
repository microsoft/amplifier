# AI-First Development Principles - Technical Specifications

## Overview

This directory contains comprehensive technical specifications for all 44 AI-First Development Architecture Principles. Each principle has its own detailed document with concrete examples, implementation guidance, anti-patterns, and cross-references to related principles.

**Purpose**: Provide both developers and AI agents with detailed, actionable guidance on implementing AI-first development practices. These specs bridge the gap between high-level principles and day-to-day implementation decisions.

## Quick Start

### For Developers

1. Browse the [Principle Index](#principle-index) below
2. Read the principle spec that applies to your current task
3. Review the Good/Bad examples for your scenario
4. Use the Implementation Checklist before committing code
5. Follow cross-references to understand related principles

### For AI Agents

These specifications are designed for AI consumption:
- Each spec is self-contained and can be used independently
- Code examples are syntactically correct and ready to adapt
- Cross-references help navigate the principle system
- Checklists provide concrete validation criteria
- Anti-patterns help avoid common failure modes

## Principle Index

### People (6 principles)

1. [Small AI-first working groups](principles/people/01-small-ai-first-working-groups.md)
2. [Strategic human touchpoints only](principles/people/02-strategic-human-touchpoints.md)
3. [Prompt engineering as core skill](principles/people/03-prompt-engineering-as-core-skill.md)
4. [Test-based verification over code review](principles/people/04-test-based-verification.md)
5. [Conversation-driven development](principles/people/05-conversation-driven-development.md)
6. [Human escape hatches always available](principles/people/06-human-escape-hatches.md)

### Process (13 principles)

7. [Regenerate, don't edit](principles/process/07-regenerate-dont-edit.md)
8. [Contract-first everything](principles/process/08-contract-first-everything.md)
9. [Tests as the quality gate](principles/process/09-tests-as-quality-gate.md)
10. [Git as safety net](principles/process/10-git-as-safety-net.md)
11. [Continuous validation with fast feedback](principles/process/11-continuous-validation-fast-feedback.md)
12. [Incremental processing as default](principles/process/12-incremental-processing-default.md)
13. [Parallel exploration by default](principles/process/13-parallel-exploration-default.md)
14. [Context management as discipline](principles/process/14-context-management-discipline.md)
15. [Git-based everything](principles/process/15-git-based-everything.md)
16. [Docs define, not describe](principles/process/16-docs-define-not-describe.md)
17. [Prompt versioning and testing](principles/process/17-prompt-versioning-testing.md)
18. [Contract evolution with migration paths](principles/process/18-contract-evolution-migration.md)
19. [Cost and token budgeting](principles/process/19-cost-token-budgeting.md)

### Technology (18 principles)

20. [Self-modifying AI-first codebase](principles/technology/20-self-modifying-ai-first-codebase.md)
21. [Limited and domain-specific by design](principles/technology/21-limited-domain-specific-design.md)
22. [Separation of concerns through layered virtualization](principles/technology/22-layered-virtualization.md)
23. [Protected self-healing kernel](principles/technology/23-protected-self-healing-kernel.md)
24. [Long-running agent processes](principles/technology/24-long-running-agent-processes.md)
25. [Simple interfaces by design](principles/technology/25-simple-interfaces-design.md)
26. [Stateless by default](principles/technology/26-stateless-by-default.md)
27. [Disposable components everywhere](principles/technology/27-disposable-components.md)
28. [CLI-first design](principles/technology/28-cli-first-design.md)
29. [Tool ecosystems as extensions](principles/technology/29-tool-ecosystems-extensions.md)
30. [Observability baked in](principles/technology/30-observability-baked-in.md)
31. [**Idempotency by design**](principles/technology/31-idempotency-by-design.md) ✨ *Example Spec*
32. [Error recovery patterns built in](principles/technology/32-error-recovery-patterns.md)
33. [Graceful degradation by design](principles/technology/33-graceful-degradation.md)
34. [Feature flags as deployment strategy](principles/technology/34-feature-flags-deployment.md)
35. [Least-privilege automation with scoped permissions](principles/technology/35-least-privilege-automation.md)
36. [Dependency pinning and security scanning](principles/technology/36-dependency-pinning-security.md)
37. [Declarative over imperative](principles/technology/37-declarative-over-imperative.md)

### Governance & Operations (7 principles)

38. [Access control and compliance as first-class](principles/governance/38-access-control-compliance.md)
39. [Metrics and evaluation everywhere](principles/governance/39-metrics-evaluation-everywhere.md)
40. [Knowledge stewardship and institutional memory](principles/governance/40-knowledge-stewardship-memory.md)
41. [Adaptive sandboxing with explicit approvals](principles/governance/41-adaptive-sandboxing.md)
42. [Data governance and privacy controls](principles/governance/42-data-governance-privacy.md)
43. [Model lifecycle management](principles/governance/43-model-lifecycle-management.md)
44. [Self-serve recovery with known-good snapshots](principles/governance/44-self-serve-recovery-snapshots.md)

## How to Use These Specifications

### During Design

When architecting a new feature or system:
1. Identify which principles apply to your design decisions
2. Read those principle specs in full
3. Review Related Principles sections to understand dependencies
4. Apply the Implementation Checklists to your design
5. Document which principles guided your choices

### During Implementation

When writing code:
1. Keep relevant principle specs open for reference
2. Use the Good/Bad examples as patterns to follow or avoid
3. Check your code against the Implementation Checklist
4. Add comments referencing which principles you're following

### During Code Review

When reviewing code (human or AI):
1. Use checklists as review criteria
2. Identify anti-patterns from the Common Pitfalls sections
3. Suggest improvements based on Good examples
4. Ensure cross-cutting concerns (like idempotency, observability) are addressed

### When Something Goes Wrong

When debugging issues:
1. Check relevant Common Pitfalls sections
2. Verify implementation against checklists
3. Review Related Principles for systemic issues
4. Update the principle spec if you discover new pitfalls

## Principle Builder Tool

The specification library includes a CLI tool for managing and maintaining principles.

### Quick Start

```bash
# List all principles
cd ai-first-principles
python3 tools/principle_builder.py list

# Validate a principle
python3 tools/principle_builder.py validate 31

# Check quality score
python3 tools/principle_builder.py check-quality 31

# Update progress statistics
python3 tools/principle_builder.py update-progress
```

### Common Operations

**Validate all specifications:**
```bash
for i in {1..44}; do python3 tools/principle_builder.py validate $i; done
```

**Quality check high-priority principles:**
```bash
for i in 7 8 9 26 31 32; do python3 tools/principle_builder.py check-quality $i; done
```

**List incomplete specifications:**
```bash
python3 tools/principle_builder.py list --status incomplete
```

### Tool Features

- **Validation**: Check specifications against quality standards
- **Quality Scoring**: Comprehensive quality metrics (structure, examples, cross-references)
- **Progress Tracking**: Automatic completion statistics by category
- **Listing**: Filter by category, status, or view all
- **Stub Generation**: Create new principle specifications from template

See [tools/README.md](tools/README.md) for complete documentation.

### Principles Demonstrated

The tool itself demonstrates AI-first principles:
- **#28 - CLI-First Design**: Command-line interface for automation
- **#29 - Tool Ecosystems**: Extends library functionality through tools
- **#25 - Simple Interfaces**: Clear, focused commands
- **#31 - Idempotency**: Validation operations are repeatable
- **#09 - Tests as Quality Gate**: Automated quality checking

## File Structure

```
ai-first-principles/
├── README.md                          # This file
├── TEMPLATE.md                        # Template for creating new specs
├── PROGRESS.md                        # Tracking completion status (44/44 complete)
├── cross-reference-index.md           # Map of principle relationships
├── tools/                             # Principle management tools
│   ├── README.md                      # Tool documentation
│   └── principle_builder.py           # CLI for validation, quality checks, listing
└── principles/
    ├── people/                        # Human-focused principles (6 specs)
    ├── process/                       # Workflow and methodology principles (13 specs)
    ├── technology/                    # Technical implementation principles (18 specs)
    └── governance/                    # Policy and operations principles (7 specs)
```

## Contributing

### Creating a New Specification

1. Copy `TEMPLATE.md`
2. Follow the naming convention: `{number}-{kebab-case-name}.md`
3. Fill in all sections with specific, actionable content
4. Include 3-5 pairs of Good/Bad code examples
5. Add cross-references to 3-6 related principles
6. Create 8-12 checklist items
7. Update `PROGRESS.md` and `cross-reference-index.md`

### Quality Standards

Each specification must have:
- Clear plain-language definition (1-2 sentences)
- AI-specific rationale (why this matters for AI agents)
- 4-6 concrete implementation approaches
- 3-5 Good/Bad example pairs with real, runnable code
- 3-6 related principles with relationship explanations
- 5-7 common pitfalls with concrete examples
- Tools organized by category with specific features noted
- 8-12 actionable checklist questions

See [Principle #31 - Idempotency by Design](principles/technology/31-idempotency-by-design.md) as the reference implementation.

## Cross-Reference System

Principles are interconnected. The [cross-reference index](cross-reference-index.md) shows:
- **Dependencies**: Principles that require others
- **Enablers**: Principles that make others possible
- **Synergies**: Principles that work better together
- **Conflicts**: Principles that trade off against each other
- **Complements**: Principles addressing related concerns

Always check cross-references when implementing a principle to understand the full context.

## Maintenance

### Version Control

This specification library is versioned:
- **v1.0**: Initial 44 principle specs
- Updates tracked in git history
- Breaking changes require major version bump

### Updates

When updating a principle spec:
1. Verify all cross-references remain valid
2. Update related principle specs if relationships change
3. Add new tools/frameworks as they emerge
4. Document new pitfalls as they're discovered
5. Keep examples current with modern practices

### Feedback

Found an error? Have a better example? Discovered a new pitfall?
- Open an issue describing the problem
- Provide specific suggestions for improvement
- Include concrete examples if proposing new content

## Related Documentation

- [AMPLIFIER_SELF_IMPROVEMENT_PHILOSOPHY.md](../AMPLIFIER_SELF_IMPROVEMENT_PHILOSOPHY.md) - High-level principles overview
- [IMPLEMENTATION_PHILOSOPHY.md](../ai_context/IMPLEMENTATION_PHILOSOPHY.md) - Ruthless simplicity guidelines
- [MODULAR_DESIGN_PHILOSOPHY.md](../ai_context/MODULAR_DESIGN_PHILOSOPHY.md) - Bricks and studs architecture

---

**Status**: In Progress (1/44 principles completed)
**Last Updated**: 2025-09-30
**Target Completion**: TBD