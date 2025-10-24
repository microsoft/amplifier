# Designer Integration with Amplifier

**Status:** ✅ Complete - Ready for Use
**Date:** 2025-10-17 (Updated: 2025-10-23)
**Integration Type:** Modular Agent Architecture

---

## Overview

The Amplified Design system is now fully integrated with Amplifier's agent architecture, providing specialized design agents and a `/designer` slash command for design system work.

## What Was Built

### 🎨 Three Specialized Design Agents

#### 1. **design-system-architect**
- **Location:** `.claude/agents/design-system-architect.md`
- **Purpose:** Strategic design system oversight
- **Responsibilities:**
  - Design token architecture
  - System-wide patterns and foundations
  - Nine Dimensions evaluation
  - Five Pillars validation
  - Cross-cutting design concerns

**When to use:**
```
Use the design-system-architect agent to create a semantic color system
```

#### 2. **component-designer**
- **Location:** `.claude/agents/component-designer.md`
- **Purpose:** Tactical component design
- **Responsibilities:**
  - Individual component design and refinement
  - Props API design
  - State handling (loading, error, empty, success)
  - Variant creation
  - Component documentation

**When to use:**
```
Use the component-designer agent to design a notification toast component
```

#### 3. **animation-choreographer**
- **Location:** `.claude/agents/animation-choreographer.md`
- **Purpose:** Motion design specialist
- **Responsibilities:**
  - Animation timing and easing
  - Micro-interactions
  - Page transitions
  - Loading states
  - Accessibility for motion

**When to use:**
```
Use the animation-choreographer agent to create a drawer slide-in animation
```

### ⚡ `/designer` Slash Command

- **Location:** `.claude/commands/designer.md`
- **Purpose:** Orchestrate design workflow
- **Modes:**
  - `/designer` - Auto-routes to appropriate agent
  - `/designer system [task]` - Direct to design-system-architect
  - `/designer component [task]` - Direct to component-designer
  - `/designer animate [task]` - Direct to animation-choreographer

## Integration Architecture

### Directory Structure

**Updated 2025-10-23:** Design agents now live in project `.claude/` directory (no longer symlinked to amplifier).

```
amplified-design/
├── .claude/                          # Project-specific agents
│   ├── agents/
│   │   ├── design-system-architect.md   # Design system specialist
│   │   ├── component-designer.md        # Component design specialist
│   │   └── animation-choreographer.md   # Motion design specialist
│   ├── commands/
│   │   └── designer.md                  # /designer slash command
│   ├── settings.json                    # Project settings
│   └── README.md                        # Agent documentation
│
├── amplifier/                        # Amplifier submodule (separate)
│   └── .claude/
│       ├── agents/                   # General-purpose agents
│       │   ├── zen-architect.md      # Code architecture
│       │   ├── modular-builder.md    # Implementation
│       │   ├── bug-hunter.md         # Debugging
│       │   └── ... (25+ agents)
│       └── commands/                 # General-purpose commands
│
├── studio-interface/                 # Implementation
├── .design/                          # Design documentation
│   ├── specs/                        # Agent-generated design specs
│   ├── ICON-ANIMATION-GUIDELINES.md
│   ├── COMPONENT-CREATION-PROTOCOL.md
│   └── ...
├── FRAMEWORK.md                      # Nine Dimensions + Four Layers
├── PHILOSOPHY.md                     # Five Pillars
├── PRINCIPLES.md                     # Quick reference
├── VISION.md                         # Beyond the artifact
├── CLAUDE.md                         # AI assistant guide
└── DESIGNER-INTEGRATION.md           # This document
```

### How Integration Works

1. **Agent Discovery**
   - Design agents live in `amplified-design/.claude/agents/` (project-specific)
   - Amplifier agents live in `amplifier/.claude/agents/` (general-purpose)
   - Claude Code discovers agents from project `.claude/` directory
   - Amplifier agents accessible via explicit reference or path
   - Available via Task tool or direct invocation

2. **Command Routing**
   - `/designer` command expands from `.claude/commands/designer.md`
   - Routes to appropriate design agent based on task
   - Provides full context and philosophy

3. **Philosophy Preservation**
   - All agents reference Amplified Design's core documents
   - Nine Dimensions and Five Pillars embedded in agent prompts
   - 9.5/10 quality baseline maintained
   - Project aesthetic enforced (see `.design/AESTHETIC-GUIDE.md`)

4. **Modular Separation**
   - Design agents: amplified-design (this project)
   - General-purpose agents: amplifier (submodule)
   - Clear ownership boundaries
   - No cross-contamination

## Usage Guide

### Basic Usage

**Automatic routing (recommended):**
```bash
/designer Create motion timing tokens for micro-interactions
```
The system analyzes your request and routes to the appropriate agent.

**Direct routing:**
```bash
/designer system Define semantic color tokens for dark mode
/designer component Design a file upload component with drag-and-drop
/designer animate Create a success checkmark draw-in animation
```

### Integration with Other Agents

Design agents work seamlessly with amplifier's ecosystem:

**Workflow Example:**
```
1. /designer component Design a modal dialog
   → component-designer creates specification

2. Use the modular-builder agent to implement the modal from the spec
   → modular-builder codes the component

3. Use the security-guardian agent to validate accessibility
   → security-guardian checks WCAG compliance

4. Use the test-coverage agent to ensure quality
   → test-coverage writes tests
```

**Common Patterns:**

| Design Task | Agent Flow |
|-------------|------------|
| New component | designer → modular-builder → test-coverage |
| Animation | designer → animation-choreographer → performance-optimizer |
| System tokens | designer → design-system-architect → modular-builder |
| Accessibility fix | security-guardian → designer → modular-builder |
| Performance issue | performance-optimizer → designer → modular-builder |

### Philosophy Application

All design agents automatically apply:

#### Nine Dimensions
1. **Style** - German car facility aesthetic
2. **Motion** - <100ms instant, 100-300ms responsive, 300-1000ms deliberate
3. **Voice** - Clear, concise, purposeful
4. **Space** - 8px system (4, 8, 12, 16, 24, 32, 48, 64, 96, 128)
5. **Color** - WCAG AA contrast (4.5:1 text, 3:1 UI)
6. **Typography** - Sora, Geist Sans, Geist Mono
7. **Proportion** - Balanced scale relationships
8. **Texture** - Purposeful depth
9. **Body** - 44x44px touch targets, keyboard navigation

#### Five Pillars
1. **Purpose Drives Execution** - Understand why before how
2. **Craft Embeds Care** - Quality in details
3. **Constraints Enable Creativity** - Structure unlocks solutions
4. **Intentional Incompleteness** - Room for contribution
5. **Design for Humans** - People, not pixels

#### Quality Standards
- 9.5/10 baseline (refined, not generic)
- WCAG AA accessibility
- 60fps performance
- Reduced motion support
- Cross-platform compatibility

## Examples

### Example 1: Design System Token Architecture

```
/designer system Create animation timing tokens that align with our motion protocol

→ Routed to: design-system-architect
→ Applies: Motion timing protocol, Nine Dimensions (Motion)
→ Output: CSS variable definitions, usage guidelines, documentation
→ Next step: modular-builder implements in globals.css
```

### Example 2: Component Design

```
/designer component Design a toast notification with success, error, and warning variants

→ Routed to: component-designer
→ Applies: All Nine Dimensions, Five Pillars, state handling
→ Output: Component specification, props API, variant designs
→ Next step: modular-builder implements component
```

### Example 3: Animation Design

```
/designer animate Create a page transition that feels smooth and maintains context

→ Routed to: animation-choreographer
→ Applies: Motion timing protocol, GPU acceleration, reduced motion
→ Output: Animation specification, timing details, accessibility fallbacks
→ Next step: modular-builder implements with Framer Motion
```

### Example 4: Multi-Agent Workflow

```
User: "I need an animated icon for file upload"

1. /designer animate Design an upload icon animation
   → animation-choreographer: Creates motion spec (arrow bounce, 300ms)

2. Use the modular-builder agent to implement the AnimatedUploadIcon
   → modular-builder: Codes the component using Framer Motion

3. Use the test-coverage agent to test the animation
   → test-coverage: Writes tests for animation states

4. Use the design-system-architect agent to review for consistency
   → design-system-architect: Validates against system patterns

Result: Fully implemented, tested, system-consistent animated icon
```

## Key Reference Documents

Design agents automatically reference:

| Document | Purpose |
|----------|---------|
| `FRAMEWORK.md` | Nine Dimensions + Four Layers methodology |
| `PHILOSOPHY.md` | Five Pillars deep dive |
| `PRINCIPLES.md` | Quick reference guide |
| `VISION.md` | Beyond the artifact philosophy |
| `CLAUDE.md` | Implementation standards and protocols |
| `CONTRIBUTING.md` | Ethical approach to design inspiration |
| `.design/COMPONENT-CREATION-PROTOCOL.md` | Component validation checklist |
| `.design/ICON-ANIMATION-GUIDELINES.md` | Animation patterns and protocols |
| `studio-interface/app/globals.css` | Design tokens (source of truth) |

## Benefits of Integration

### 1. **Specialized Expertise**
- Design-focused agents understand design philosophy deeply
- Apply Nine Dimensions and Five Pillars automatically
- Maintain 9.5/10 quality baseline consistently

### 2. **Seamless Workflow**
- `/designer` command provides single entry point
- Auto-routing simplifies agent selection
- Integrates with existing amplifier agents

### 3. **Philosophy Preservation**
- Design decisions grounded in framework
- Quality standards enforced systematically
- German car facility aesthetic maintained

### 4. **Scalable System**
- Easy to extend with new design agents
- Follows amplifier's proven patterns
- Documentation-driven approach

### 5. **Cross-Agent Collaboration**
- Design agents work with zen-architect, modular-builder, etc.
- Clear handoff patterns established
- End-to-end workflows supported

## Testing the Integration

### Smoke Test

Try these commands to verify integration:

```bash
# 1. Check agent availability
Use the design-system-architect agent to list available design tokens

# 2. Test slash command
/designer What are the Nine Dimensions?

# 3. Test direct routing
/designer system Explain our motion timing protocol

# 4. Test component design
/designer component What makes a good button component?

# 5. Test animation
/designer animate What's the difference between instant, responsive, and deliberate timing?
```

### Expected Behavior

When you invoke `/designer`:
1. Command expands from `designer.md`
2. Routes to appropriate agent (or auto-selects)
3. Agent applies Nine Dimensions and Five Pillars
4. Response includes design rationale
5. Quality meets 9.5/10 baseline

### Validation Checklist

- [ ] `/designer` command appears in available commands list
- [ ] Can invoke design-system-architect directly
- [ ] Can invoke component-designer directly
- [ ] Can invoke animation-choreographer directly
- [ ] Agents reference correct documentation
- [ ] Philosophy is applied in responses
- [ ] Quality standards are maintained

## Comparison: Before vs After

### Before Integration

**Problem:**
- Design decisions made ad-hoc
- Philosophy not systematically applied
- No specialized design expertise
- Manual agent selection required
- Inconsistent quality

**Workflow:**
```
User asks for design → Use zen-architect → Hope it knows design philosophy
```

### After Integration

**Solution:**
- Design agents with embedded philosophy
- Nine Dimensions and Five Pillars automatically applied
- Specialized expertise for system, component, and motion
- Single `/designer` command with auto-routing
- Consistent 9.5/10 quality

**Workflow:**
```
User asks for design → /designer → Routed to specialist → Philosophy applied → Quality assured
```

## Next Steps (Optional Enhancements)

While the integration is complete and functional, future enhancements could include:

### Phase 2: Advanced Features
- [ ] Multi-step startup hooks for design validation
- [ ] Automated design token validation
- [ ] Visual regression testing integration
- [ ] Component playground generation
- [ ] Design system metrics tracking

### Phase 3: Extended Ecosystem
- [ ] typography-designer agent (specialized for type system)
- [ ] accessibility-designer agent (WCAG deep-dive)
- [ ] illustration-designer agent (iconography, visual assets)
- [ ] content-designer agent (copy, voice, tone)

### Phase 4: Tooling
- [ ] `make design-*` commands in Makefile
- [ ] Design system documentation generator
- [ ] Component specification templates
- [ ] Animation preview playground

## Troubleshooting

### Command Not Found

**Issue:** `/designer` command doesn't appear

**Solution:**
```bash
# Verify file exists
ls .claude/commands/designer.md

# Check if .claude is a symlink to amplifier/.claude
ls -la .claude

# Restart Claude Code if needed
```

### Agent Not Routing Correctly

**Issue:** Wrong agent selected for task

**Solution:**
Use direct routing:
```bash
/designer system [task]      # Force design-system-architect
/designer component [task]   # Force component-designer
/designer animate [task]     # Force animation-choreographer
```

### Philosophy Not Applied

**Issue:** Responses don't reference Nine Dimensions or Five Pillars

**Solution:**
```bash
# Explicitly request philosophy application
/designer Apply the Nine Dimensions framework to [task]

# Or reference documents directly
Review @FRAMEWORK.md and then [task]
```

## Success Metrics

Integration succeeds when:
- ✅ Design agents accessible via Task tool
- ✅ `/designer` command works
- ✅ Auto-routing selects correct specialist
- ✅ Philosophy automatically applied
- ✅ Quality consistently at 9.5/10
- ✅ Workflow integrates with amplifier agents
- ✅ Documentation is referenced correctly
- ✅ Developers use system confidently

## Conclusion

The Amplified Design system is now fully integrated with Amplifier's agent architecture, providing:

1. **Three specialized design agents** with embedded philosophy
2. **One unified `/designer` command** for orchestration
3. **Seamless integration** with amplifier's 25 existing agents
4. **Consistent quality** through systematic philosophy application
5. **Scalable foundation** for future design system evolution

**The artifact is the container. The experience is the product. The agents are the guides.**

Use `/designer` to create refined, purposeful, human-centered design work that embodies the Nine Dimensions and Five Pillars.

---

**Ready to use!** Try: `/designer What can you help me with?`
