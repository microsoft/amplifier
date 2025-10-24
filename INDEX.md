# Amplified Design - Documentation Index

**Last updated**: 2025-10-23 10:10
**Specs**: 2 | **Active Work**: 2

---

## Quick Start

**New to the project?**
1. [PHILOSOPHY.md](./PHILOSOPHY.md) - Five Pillars (Purpose, Craft, Constraints, Incompleteness, Humans)
2. [FRAMEWORK.md](./FRAMEWORK.md) - Nine Dimensions + Four Layers methodology
3. [COMPONENT-CREATION-PROTOCOL.md](./.design/COMPONENT-CREATION-PROTOCOL.md) - Checklist for creating components

**Building a feature?**
1. Check [Design Specs](./.design/specs/INDEX.md) for existing patterns
2. Consult [Aesthetic Guide](./.design/AESTHETIC-GUIDE.md) for emotional tone
3. Follow [Component Protocol](./.design/COMPONENT-CREATION-PROTOCOL.md) checklist

---

## Documentation Hierarchy

### Philosophy (Root Level)
**Foundation**: Core principles and methodology

- [FRAMEWORK.md](./FRAMEWORK.md) - Nine Dimensions (Style, Motion, Voice, Space, Color, Typography, Proportion, Texture, Body) + Four Layers (Purpose, Expression, Context, Adaptation)
- [PHILOSOPHY.md](./PHILOSOPHY.md) - Five Pillars deep dive
- [PRINCIPLES.md](./PRINCIPLES.md) - Quick reference guide
- [VISION.md](./VISION.md) - Beyond the artifact philosophy
- [CLAUDE.md](./CLAUDE.md) - AI assistant implementation guide

### Design Layer (.design/)
**Protocols + Specifications**: How to create quality components

**Core Protocols** (always active):
- [COMPONENT-CREATION-PROTOCOL.md](./.design/COMPONENT-CREATION-PROTOCOL.md) - Pre/during/post creation checklist
- [PROACTIVE-DESIGN-PROTOCOL.md](./.design/PROACTIVE-DESIGN-PROTOCOL.md) - Aesthetic-first workflow
- [DESIGN-SYSTEM-ENFORCEMENT.md](./.design/DESIGN-SYSTEM-ENFORCEMENT.md) - No hardcoded values rule
- [ANTI-PATTERNS.md](./.design/ANTI-PATTERNS.md) - Common mistakes to avoid

**Design Specifications** ([see all](./.design/specs/INDEX.md)):
- Agent-generated specs for features and components
- Includes rationale, decisions, and implementation requirements
- [View specs index](./.design/specs/INDEX.md)

**Active Work** (.design/active/):
- Current features in progress
- Status-prefixed: ACTIVE, TODO, BLOCKED

### Project Layer (studio-interface/)
**Implementation**: Current project specifications

- [IMPLEMENTATION-SPEC.md](./studio-interface/IMPLEMENTATION-SPEC.md) - Studio interface current state
- [Project documentation](./studio-interface/docs/)

### AI Working (ai_working/)
**Studio-Specific AI Tools**: Workspace for AI-powered Studio features

- [discovery_processor/](./ai_working/discovery_processor/) - Processes content for Discovery canvas (images, docs, URLs, sketches)
- [ai_working/README.md](./ai_working/README.md) - AI tools documentation and usage patterns
- See `amplifier/ai_working/` for general-purpose AI tools

### Agents (Multi-Level Architecture)

**Project Design Agents** (.claude/agents/):
- [animation-choreographer.md](./.claude/agents/animation-choreographer.md) - Motion design specialist (timing, easing, micro-interactions)
- [component-designer.md](./.claude/agents/component-designer.md) - Tactical component design (props API, states, variants)
- [design-system-architect.md](./.claude/agents/design-system-architect.md) - Strategic system oversight (tokens, Nine Dimensions, Five Pillars)

**Project Command** (.claude/commands/):
- `/designer` - Orchestrates design workflow with automatic agent routing

**General-Purpose Agents** (amplifier/.claude/agents/):
- zen-architect - Code architecture analysis and design
- modular-builder - Implementation from specifications
- bug-hunter - Systematic bug finding and fixing
- test-coverage - Test analysis and suggestions
- security-guardian - Security reviews and accessibility validation
- performance-optimizer - Performance analysis and optimization
- [See amplifier/.claude/agents/ for full list of 25+ agents]

**Framework Agents** (agents/):
- [ux-wireframe-designer.md](./agents/ux-wireframe-designer.md) - Generate UX specifications
- [design-diagnostics.md](./agents/design-diagnostics.md) - Diagnose design issues
- [customization-guide.md](./agents/customization-guide.md) - Safe customization guidance
- [quality-guardian.md](./agents/quality-guardian.md) - Validate quality (WCAG AA, 9.5/10 baseline)
- [orchestrator.md](./agents/orchestrator.md) - Coordinate multi-agent workflows

**See [.claude/README.md](./.claude/README.md) for complete agent documentation.**

---

## Quick Reference by Role

### For Developers
**"I need to implement a feature"**
1. [COMPONENT-CREATION-PROTOCOL.md](./.design/COMPONENT-CREATION-PROTOCOL.md) (5-min checklist)
2. [Design Specs](./.design/specs/INDEX.md) (check for existing patterns)
3. Validate: `npm run validate:tokens && npx tsc --noEmit`

### For Designers
**"I need to design a feature"**
1. [FRAMEWORK.md](./FRAMEWORK.md) (Nine Dimensions methodology)
2. [AESTHETIC-GUIDE.md](./.design/AESTHETIC-GUIDE.md) (project emotional tone)
3. [ux-wireframe-designer.md](./agents/ux-wireframe-designer.md) (agent generates specs)

### For AI Agents
**"I need to generate specifications"**
1. [PHILOSOPHY.md](./PHILOSOPHY.md) (Five Pillars: guide all decisions)
2. [COMPONENT-CREATION-PROTOCOL.md](./.design/COMPONENT-CREATION-PROTOCOL.md) (checklist to follow)
3. [Design Specs](./.design/specs/INDEX.md) (reference past decisions)

---

## Search Patterns

**Find existing specs**: `grep -r "feature-name" .design/specs/`
**Find by tag**: `grep -l "tags:.*animation" .design/specs/*.md`
**Find active work**: `ls .design/active/ACTIVE-*.md`
**Find recent specs**: `find .design/specs -name "*.md" -mtime -30`

---

## Validation Commands

```bash
# Validate CSS variables (no hardcoded values)
npm run validate:tokens

# TypeScript type checking
npx tsc --noEmit

# Production build
npm run build
```

All validations must pass before committing.

---

**The artifact is the container. The experience is the product. The values are the legacy.**

Design accordingly.
