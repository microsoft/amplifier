# Amplified Design Agents & Commands

This directory contains project-specific Claude Code agents and commands for the Amplified Design system.

## Project Structure

```
amplified-design/
├── .claude/                           # THIS DIRECTORY - Project agents
│   ├── agents/
│   │   ├── animation-choreographer.md  # Motion design specialist
│   │   ├── component-designer.md       # Component design specialist
│   │   └── design-system-architect.md  # System architecture specialist
│   ├── commands/
│   │   └── designer.md                 # /designer slash command
│   └── settings.json                   # Project settings
│
├── amplifier/                         # Submodule (general-purpose agents)
│   └── .claude/
│       ├── agents/
│       │   ├── zen-architect.md       # Code architecture
│       │   ├── modular-builder.md     # Implementation
│       │   ├── bug-hunter.md          # Debugging
│       │   └── ... (25+ general-purpose agents)
│       └── commands/
│           └── ... (general-purpose commands)
│
└── studio-interface/                  # Optional nested agents
    └── .claude/
        └── agents/
            ├── ux-wireframe-designer.md
            └── requirements-architect.md
```

## Design Agents (This Directory)

### animation-choreographer
**Purpose:** Motion design specialist for purposeful animations

**Use for:**
- Icon animations and micro-interactions
- Page transitions and choreography
- Loading states and progress indicators
- Motion timing and easing decisions
- Accessibility considerations for motion

**Invoke via:**
```
Use the animation-choreographer agent to design a drawer slide-in animation
```

or via `/designer` command:
```
/designer animate Create a drawer slide-in animation
```

---

### component-designer
**Purpose:** Tactical component design specialist

**Use for:**
- Designing new UI components
- Refining existing components
- Component-level design decisions
- Aesthetic implementation
- Component documentation and examples
- Variant design and props API

**Invoke via:**
```
Use the component-designer agent to design a notification toast component
```

or via `/designer` command:
```
/designer component Design a notification toast with all states
```

---

### design-system-architect
**Purpose:** Strategic design system overseer

**Use for:**
- Design system architecture and token design
- Establishing design foundations (color, typography, spacing, motion)
- Evaluating design decisions against Nine Dimensions
- Validating Five Pillars alignment
- Design philosophy application and guidance
- Cross-cutting design concerns

**Invoke via:**
```
Use the design-system-architect agent to create semantic color tokens
```

or via `/designer` command:
```
/designer system Create semantic color tokens for dark mode
```

## Slash Commands (This Directory)

### /designer
**Purpose:** Orchestrate design workflow with automatic agent routing

**Usage:**
```bash
# Auto-route to appropriate specialist
/designer [your design task]

# Direct routing
/designer system [task]      # → design-system-architect
/designer component [task]   # → component-designer
/designer animate [task]     # → animation-choreographer
```

**Examples:**
```bash
/designer Create motion timing tokens for our design system
/designer component Design a button with primary, secondary, and ghost variants
/designer animate Animate a success checkmark that draws in over 300ms
```

See [.claude/commands/designer.md](.claude/commands/designer.md) for full documentation.

## Amplifier Agents (Submodule)

General-purpose agents from the Amplifier submodule are available for use but live in `amplifier/.claude/agents/`.

**Commonly used Amplifier agents:**
- `zen-architect` - Code architecture analysis and design
- `modular-builder` - Implementation from specifications
- `bug-hunter` - Systematic bug finding and fixing
- `test-coverage` - Test analysis and suggestions
- `security-guardian` - Security reviews and accessibility
- `performance-optimizer` - Performance analysis and optimization

**How to use Amplifier agents:**
```
Use the zen-architect agent to analyze the code architecture
Use the modular-builder agent to implement this specification
```

Claude Code can access them via implicit path resolution or explicit reference to `amplifier/.claude/agents/[agent-name]`.

## Design Philosophy

All design agents embody:

### Nine Dimensions
1. Style - Visual language
2. Motion - Timing and communication
3. Voice - Language and tone
4. Space - Layout and hierarchy
5. Color - Meaning and accessibility
6. Typography - Hierarchy and legibility
7. Proportion - Scale relationships
8. Texture - Depth and materiality
9. Body - Ergonomics and accessibility

### Five Pillars
1. Purpose Drives Execution
2. Craft Embeds Care
3. Constraints Enable Creativity
4. Intentional Incompleteness
5. Design for Humans

See [FRAMEWORK.md](../FRAMEWORK.md), [PHILOSOPHY.md](../PHILOSOPHY.md), and [PRINCIPLES.md](../PRINCIPLES.md) for complete philosophy.

## Workflow Patterns

### Design → Implement → Validate
```
1. /designer component Design a modal dialog
   → component-designer creates specification

2. Use the modular-builder agent to implement the modal from spec
   → modular-builder codes the component

3. Use the security-guardian agent to validate accessibility
   → security-guardian checks WCAG compliance

4. Use the test-coverage agent to ensure quality
   → test-coverage writes tests
```

### System-Level Design
```
1. /designer system Define animation timing tokens
   → design-system-architect creates token specifications

2. Use the modular-builder agent to implement in globals.css
   → modular-builder adds CSS variables

3. Use the design-system-architect agent to review consistency
   → Validates system coherence
```

## Quality Standards

All design work maintains:
- **9.5/10 baseline** - Refined, not generic
- **WCAG AA accessibility** - Works for everyone
- **60fps performance** - Smooth animations
- **Reduced motion support** - Respects user preferences
- **Touch targets** - 44x44px minimum

## Key Files Referenced

Design agents automatically reference:
- `FRAMEWORK.md` - Nine Dimensions + Four Layers
- `PHILOSOPHY.md` - Five Pillars deep dive
- `PRINCIPLES.md` - Quick reference
- `VISION.md` - Beyond the artifact
- `CLAUDE.md` - Implementation standards
- `.design/COMPONENT-CREATION-PROTOCOL.md` - Component checklist
- `.design/AESTHETIC-GUIDE.md` - Project aesthetic (if exists)
- `studio-interface/app/globals.css` - Design tokens

## Modifying This Directory

**DO:**
- ✅ Add project-specific design agents
- ✅ Update design agent specifications
- ✅ Add project-specific slash commands
- ✅ Document new agents in this README

**DON'T:**
- ❌ Add general-purpose agents (those go in amplifier)
- ❌ Modify amplifier submodule agents
- ❌ Copy amplifier agents here (reference them instead)
- ❌ Add agents unrelated to design philosophy

## Contributing

When adding new design agents:
1. Follow existing agent format (YAML frontmatter + Markdown)
2. Ensure Nine Dimensions and Five Pillars alignment
3. Document in this README
4. Reference core philosophy documents
5. Include examples and usage patterns

---

**The artifact is the container. The experience is the product. Design for humans, not screens.**
