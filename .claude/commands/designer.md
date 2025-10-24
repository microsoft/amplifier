# Designer Command

**Invoke the Amplified Design workflow for design system and component work.**

## What This Does

The `/designer` command activates the Amplified Design workflow, orchestrating specialized design agents to handle design system architecture, component design, and motion choreography following the Nine Dimensions and Five Pillars philosophy.

## When to Use

Use `/designer` when you need to:
- Design or refactor components
- Establish design system architecture
- Create or refine animations
- Evaluate design decisions
- Apply Nine Dimensions framework
- Validate Five Pillars alignment
- Implement design tokens
- Document design patterns

## Available Modes

### `/designer` (General Mode)
Analyzes the request and automatically selects the appropriate specialist agent:
- **design-system-architect** - For system-level design decisions
- **component-designer** - For individual component work
- **animation-choreographer** - For motion design

### `/designer system [task]`
Directly invoke **design-system-architect** for:
- Design token architecture
- System-wide patterns
- Foundation design (color, typography, spacing, motion)
- Cross-cutting concerns
- Philosophy application

**Example:**
```
/designer system Create a semantic color system for dark mode
```

### `/designer component [task]`
Directly invoke **component-designer** for:
- Individual component design
- Component refinement
- Props API design
- State handling
- Variant creation

**Example:**
```
/designer component Design a notification toast with all states
```

### `/designer animate [task]`
Directly invoke **animation-choreographer** for:
- Motion design
- Animation timing
- Micro-interactions
- Page transitions
- Loading states

**Example:**
```
/designer animate Create a drawer slide-in animation
```

## How It Works

The designer workflow follows these steps:

1. **Understand Context**
   - Review existing design system
   - Understand requirements
   - Identify constraints

2. **Select Specialist**
   - Route to appropriate agent based on task
   - Provide full context to specialist

3. **Apply Philosophy**
   - Evaluate through Nine Dimensions
   - Validate against Five Pillars
   - Ensure 9.5/10 quality baseline

4. **Generate Specification**
   - Create detailed design spec
   - Document rationale
   - Provide implementation guidance

5. **Validate & Refine**
   - Check system consistency
   - Validate accessibility
   - Ensure protocol compliance

## Design Philosophy Integration

All designer work follows:

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

## Quality Standards

Designer ensures:
- **9.5/10 baseline** - Refined, not generic
- **WCAG AA accessibility** - Works for everyone
- **Performance** - 60fps animations
- **Consistency** - Follows system patterns
- **Documentation** - Clear usage guidance

## Example Usage

### System-Level Design
```
/designer Create motion timing tokens for our design system
```
Routes to: **design-system-architect**

### Component Design
```
/designer Design a button component with primary, secondary, and ghost variants
```
Routes to: **component-designer**

### Motion Design
```
/designer Animate a success checkmark that draws in over 300ms
```
Routes to: **animation-choreographer**

### Evaluation
```
/designer Review this component for Nine Dimensions compliance
```
Routes to: **design-system-architect** (REVIEW mode)

### Refinement
```
/designer Improve the loading state animation to feel more responsive
```
Routes to: **animation-choreographer** (REFINE mode)

## Integration with Amplifier

The designer workflow integrates with amplifier's broader agent ecosystem:

**Collaborates with:**
- `zen-architect` - Code architecture and analysis
- `modular-builder` - Implementation from design specs
- `bug-hunter` - Fixing design implementation issues
- `security-guardian` - Accessibility validation
- `performance-optimizer` - Performance tuning
- `test-coverage` - Quality assurance

**Complements:**
- Design specs → `modular-builder` implements
- Accessibility concerns → `security-guardian` validates
- Performance issues → `performance-optimizer` resolves
- Motion bugs → `bug-hunter` debugs

## Key Files & References

The designer agents reference:
- `@FRAMEWORK.md` - Nine Dimensions + Four Layers
- `@PHILOSOPHY.md` - Five Pillars deep dive
- `@PRINCIPLES.md` - Quick reference
- `@VISION.md` - Beyond the artifact
- `@CLAUDE.md` - Implementation standards
- `@CONTRIBUTING.md` - Ethical approach
- `@.design/COMPONENT-CREATION-PROTOCOL.md` - Component checklist
- `@.design/ICON-ANIMATION-GUIDELINES.md` - Animation patterns
- `@studio-interface/app/globals.css` - Design tokens

## Aesthetic

All designer output maintains:
- Clean, precise, geometric
- Restrained, purposeful
- Quality through subtle refinement
- 9.5/10 polish level
- No decoration for decoration's sake

## Success Criteria

Designer workflow succeeds when:
- Purpose is crystal clear
- Philosophy is embodied
- Quality meets 9.5/10 baseline
- Accessibility standards met
- System consistency maintained
- Documentation is complete
- Implementation is straightforward

---

## Quick Start

**Most common usage:**
```bash
/designer [your design task]
```

The system will automatically route to the appropriate specialist and apply the full design philosophy to deliver refined, purposeful solutions.

**Remember:** The artifact is the container. The experience is the product. Design for humans, not screens.
