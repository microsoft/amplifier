# Design Intelligence Capability

This directory contains Amplifier's integrated design intelligence capability that provides reusable design methodology, knowledge, and specialist agents for any project.

## Overview

Amplifier now includes comprehensive design intelligence that combines:
- **Design Philosophy** - Core design thinking and principles
- **Knowledge Base** - Evidence-based design knowledge
- **Design Protocols** - Reusable process templates and guidelines
- **Design Specialists** - 7 specialized AI agents
- **Orchestration** - `/designer` command for coordinating design work

## Structure

```
docs/design/
├── README.md (this file)
├── knowledge-base/
│   ├── README.md - Knowledge base overview
│   ├── color-theory.md - Color science, WCAG contrast, color psychology
│   ├── animation-principles.md - 12 animation principles, easing, timing
│   ├── accessibility.md - WCAG 2.1 standards, POUR principles
│   └── typography.md - Type scales, font systems, responsive text
└── protocols/
    ├── COMPONENT-CREATION-PROTOCOL.md - Component design checklist
    ├── DESIGN-CHECKLIST.md - Nine dimensions evaluation
    ├── ANTI-PATTERNS.md - Common design mistakes to avoid
    ├── WIREFRAME-STANDARDS.md - Wireframe guidelines
    └── REQUIREMENTS-TEMPLATE.md - Design requirements template
```

## Philosophy Documents

Core design philosophy is located in `ai_context/` alongside software development philosophy:

- **`ai_context/DESIGN-PHILOSOPHY.md`** - Five Pillars deep dive
- **`ai_context/DESIGN-PRINCIPLES.md`** - Quick reference guide
- **`ai_context/design/DESIGN-FRAMEWORK.md`** - 9 Dimensions + 4 Layers methodology
- **`ai_context/design/DESIGN-VISION.md`** - Beyond the artifact philosophy

These are automatically imported via `@CLAUDE.md` for all Claude Code sessions.

## Design Agents

Seven specialist agents are available in `.claude/agents/`:

1. **animation-choreographer** - Motion design and transitions
2. **art-director** - Aesthetic strategy and visual direction
3. **component-designer** - Component design and creation
4. **design-system-architect** - Design system architecture
5. **layout-architect** - Information architecture and layout
6. **responsive-strategist** - Device adaptation and responsive design
7. **voice-strategist** - Voice & tone for UI copy

## Using Design Intelligence

### Via /designer Command

The `/designer` command orchestrates design work by routing tasks to appropriate specialists:

```
/designer create a button component with hover states
```

The command will:
1. Analyze your request
2. Select appropriate specialist(s)
3. Coordinate their work
4. Deliver comprehensive design output

### Directly with Agents

You can also invoke design agents directly using the Task tool:

```
Task with subagent_type="component-designer": "Design a button component..."
```

### Referencing Knowledge Base

Design agents automatically reference the knowledge base. You can also reference it directly:

```
@docs/design/knowledge-base/color-theory.md
@docs/design/protocols/COMPONENT-CREATION-PROTOCOL.md
```

## Design Philosophy Summary

### The Nine Dimensions

All design work evaluates against nine dimensions:
1. **Purpose** - Why does this exist?
2. **Visual Hierarchy** - What should users notice first?
3. **Color & Contrast** - Are colors accessible and meaningful?
4. **Typography** - Is text readable and scannable?
5. **Spacing** - Does whitespace guide the eye?
6. **Responsive Design** - Does it work on all devices?
7. **Accessibility** - Can everyone use it?
8. **Motion** - Does animation serve a purpose?
9. **Voice** - Is the copy clear and appropriate?

### The Four Layers

Design operates at four integrated layers:
1. **Foundational** - Tokens, typography, color systems
2. **Structural** - Layout, spacing, grid systems
3. **Behavioral** - Interactions, animations, states
4. **Experiential** - Complete user journeys

### Core Principles

1. **User vision transformed** - Take user's raw ideas and refine them
2. **Evidence-based decisions** - Use knowledge base, not trends
3. **Accessible by default** - WCAG 2.1 AA minimum
4. **Purposeful, not decorative** - Every element serves a function
5. **Technically implementable** - Design within web platform constraints

## Project-Specific Design Files

When working on a project, design agents create project-specific files:

- **`.design/AESTHETIC-GUIDE.md`** - Project visual direction (created by art-director)
- **`.design/specs/[feature]-[date].md`** - Design specifications per feature

These are separate from the reusable design capability in this directory.

## Integration with Software Development

Design intelligence integrates seamlessly with Amplifier's software development philosophy:

- **Ruthless simplicity** applies to both code and design
- **Modular design philosophy** - Components are self-contained bricks
- **Analysis-first** - Understand before designing/implementing
- **Test-driven** - Design specifications precede implementation

## Next Steps

1. **Explore the knowledge base** - Understand the evidence-based design foundation
2. **Review design protocols** - Learn the design process workflows
3. **Try /designer** - Experience orchestrated design intelligence
4. **Read philosophy docs** - Understand the design thinking framework
