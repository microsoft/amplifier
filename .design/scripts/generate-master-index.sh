#!/bin/bash
# Generate root INDEX.md from file structure

cd "$(dirname "$0")/../.."

# Count specs and active files
SPEC_COUNT=$(ls -1 .design/specs/*.md 2>/dev/null | grep -v INDEX.md | grep -v TEMPLATE.md | wc -l | tr -d ' ')
ACTIVE_COUNT=$(ls -1 .design/active/ACTIVE-*.md 2>/dev/null | wc -l | tr -d ' ')

cat > INDEX.md <<EOF
# Amplified Design - Documentation Index

**Last updated**: $(date +"%Y-%m-%d %H:%M")
**Specs**: ${SPEC_COUNT} | **Active Work**: ${ACTIVE_COUNT}

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

### Agents (agents/)
**Framework**: Reusable, aesthetic-agnostic agent definitions

- [ux-wireframe-designer.md](./agents/ux-wireframe-designer.md) - Generate UX specifications
- [design-diagnostics.md](./agents/design-diagnostics.md) - Diagnose design issues
- [customization-guide.md](./agents/customization-guide.md) - Safe customization guidance
- [quality-guardian.md](./agents/quality-guardian.md) - Validate quality (WCAG AA, 9.5/10 baseline)
- [orchestrator.md](./agents/orchestrator.md) - Coordinate multi-agent workflows

---

## Quick Reference by Role

### For Developers
**"I need to implement a feature"**
1. [COMPONENT-CREATION-PROTOCOL.md](./.design/COMPONENT-CREATION-PROTOCOL.md) (5-min checklist)
2. [Design Specs](./.design/specs/INDEX.md) (check for existing patterns)
3. Validate: \`npm run validate:tokens && npx tsc --noEmit\`

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

**Find existing specs**: \`grep -r "feature-name" .design/specs/\`
**Find by tag**: \`grep -l "tags:.*animation" .design/specs/*.md\`
**Find active work**: \`ls .design/active/ACTIVE-*.md\`
**Find recent specs**: \`find .design/specs -name "*.md" -mtime -30\`

---

## Validation Commands

\`\`\`bash
# Validate CSS variables (no hardcoded values)
npm run validate:tokens

# TypeScript type checking
npx tsc --noEmit

# Production build
npm run build
\`\`\`

All validations must pass before committing.

---

**The artifact is the container. The experience is the product. The values are the legacy.**

Design accordingly.
EOF

echo "Generated INDEX.md"
