# Claude.md - AI Assistant Guide for Amplified Design

## Project Overview

**Studio** is a design intelligence system—not just a tool for designers, but a partner for anyone building meaningful products. It's the first design system that works like a designer, guiding through purpose, context, expression, and adaptation.

### Core Problem Being Solved
AI-generated designs are generic (5/10 quality). Customization breaks the few good parts. Every output looks the same.

### Studio's Approach
- Start with exceptional components (9.5/10 baseline)
- Guide through purpose-first design methodology
- Customize intelligently within quality guardrails
- Generate working prototypes, not just mockups
- Learn your sensibility over time

## Critical Protocol: The Foundation

**BEFORE creating or modifying ANY component, you MUST validate against:**
`.design/COMPONENT-CREATION-PROTOCOL.md`

### Non-Negotiable Requirements

1. **CSS Variables**: All variables MUST be defined in `studio-interface/app/globals.css` BEFORE use
   - Run `npm run validate:tokens` after any changes
   - Zero undefined variables allowed in production

2. **Design System Compliance**:
   - Spacing: 8px system only (4, 8, 12, 16, 24, 32, 48, 64, 96, 128)
   - Fonts: Sora (headings), Geist Sans (body), Geist Mono (code), Source Code Pro (code)
   - No emojis as UI elements
   - No Unicode characters as icons (use Icon component)

3. **Accessibility**:
   - Touch targets: 44x44px minimum (Apple) or 48x48dp (Android)
   - Contrast: 4.5:1 for text, 3:1 for UI components
   - Keyboard navigation required
   - Screen reader compatible

4. **Motion Timing**:
   - <100ms: Instant feedback (hover states)
   - 100-300ms: Responsive (button presses)
   - 300-1000ms: Deliberate (modals, transitions)
   - >1000ms: Progress indication required

5. **State Coverage**:
   - Loading state
   - Error state
   - Empty state
   - Success state

### Validation Workflow

```
1. Purpose Check → Can articulate WHY in one sentence?
2. Token Audit → All CSS variables defined?
3. Nine Dimensions → Style, Motion, Voice, Space, Color, Typography, Proportion, Texture, Body
4. Five Pillars → Purpose, Craft, Constraints, Incompleteness, Humans
5. Write Code
6. Validate → npm run validate:tokens && npx tsc --noEmit
7. Ship
```

## The Design Philosophy: Four Layers

Studio guides through a proven methodology. Every decision must be evaluated through these layers:

### Layer 1: Purpose & Intent (What and Why)
**What should exist and why?**
- Clarify the problem you're solving
- Define who it's for
- Establish values it should embody

**Questions to answer:**
- Should this exist? (Necessity)
- What problem does this solve? (Function)
- For whom? (Audience)
- Why now? (Timing and context)
- What values does this embody? (Ethics)

### Layer 2: Expression & Manifestation (How)
**How should it look, feel, and behave?**

**Nine Dimensions of Design:**
1. **Style**: Visual language matching your values
2. **Motion**: Timing that communicates intention
3. **Voice**: Language expressing personality
4. **Space**: Layout creating hierarchy
5. **Color**: Meaningful and accessible choices
6. **Typography**: Guiding attention effectively
7. **Proportion**: Scale relationships that feel right
8. **Texture**: Depth and materiality
9. **Body**: Physical ergonomics for real humans

### Layer 3: Context & Appropriateness (For Whom)
**Where and when does this work?**
- Cultural context and meanings
- Audience expectations
- Industry conventions
- When to follow or break patterns

### Layer 4: Contextual Adaptation (How Context Shapes Expression)
**How does it adapt across modalities?**
- Desktop (precision, rich information)
- Mobile (thumb zones, simplified)
- Voice (conversational, sequential)
- Emerging platforms (AR/VR, spatial)

## The Five Pillars

Every design decision should embody these principles:

1. **Purpose Drives Execution** - Understand why before perfecting how
2. **Craft Embeds Care** - Quality shows in the details
3. **Constraints Enable Creativity** - Structure unlocks better solutions
4. **Intentional Incompleteness** - Leave room for contribution
5. **Design for Humans** - People, not pixels

## Beyond the Artifact

**Remember:** The code is just the container, not the product.

When you ship a button component, you're shipping:
- How someone **feels** when they click it
- What **values** your team embodies
- What **culture** you're creating
- What **impact** you have on the world

### Three Levels of Experience

1. **Individual Experience**: Do they feel heard, confirmed, respected, trust?
2. **Social Experience**: Do teams feel empowered, confident, collaborative, proud?
3. **Cultural Experience**: Does it shift expectations, demand accessibility, question mediocrity?

## Project Structure

```
amplified-design/
├── studio-interface/          # Next.js app - main Studio interface
│   ├── app/
│   │   ├── globals.css       # ALL CSS variables defined here
│   │   └── ...
│   ├── components/
│   │   └── icons/Icon.tsx    # Icon system (24x24 grid, 2px stroke)
│   ├── state/store.ts        # Zustand global state
│   └── ...
├── packages/                  # Modular packages
│   └── interactions/         # Common interaction patterns
├── components/               # Design components library
├── agents/                   # AI agents for guidance
├── quality-guardrails/       # Validation rules
├── knowledge-base/           # Design theory documentation
├── .design/                  # Design documentation and checklists
│   └── COMPONENT-CREATION-PROTOCOL.md
├── FRAMEWORK.md             # Complete design sensibility framework
├── PHILOSOPHY.md            # Five Pillars deep dive
├── PRINCIPLES.md            # Quick reference guide
├── VISION.md                # Beyond the artifact philosophy
└── README.md                # Project overview
```

## Key Files to Reference

- `studio-interface/app/globals.css` - All CSS variables MUST be defined here
- `studio-interface/state/store.ts` - Zustand global state management
- `studio-interface/components/icons/Icon.tsx` - Icon system
- `.design/COMPONENT-CREATION-PROTOCOL.md` - Component creation rules
- `FRAMEWORK.md` - Nine dimensions + Four layers methodology
- `PHILOSOPHY.md` - Five Pillars theoretical grounding
- `PRINCIPLES.md` - Quick reference for daily practice
- `VISION.md` - The "beyond the artifact" philosophy

## Development Commands

```bash
# Validate design tokens (run after any globals.css changes)
npm run validate:tokens

# TypeScript type checking
npx tsc --noEmit

# Build project
npm run build

# Development server
npm run dev

# Install dependencies
npm install
```

## Aesthetic: German Car Facility

Think precision manufacturing facility, not flashy showroom:
- Clean, precise, geometric
- Restrained, purposeful
- Quality through subtle refinement
- 9.5/10 polish level
- No decoration for decoration's sake

## Working with Components

### Before Creating/Modifying a Component

1. **Articulate Purpose** (one clear sentence)
2. **Validate Need** (should this exist?)
3. **Check Tokens** (all CSS variables defined in globals.css?)
4. **Evaluate Against Nine Dimensions**:
   - Style: Visual language appropriate?
   - Motion: Timing follows protocol (<100ms, 100-300ms, 300-1000ms)?
   - Voice: Language matches personality?
   - Space: Follows 8px spacing system?
   - Color: Meets contrast requirements (4.5:1 text, 3:1 UI)?
   - Typography: Hierarchy clear and using system fonts?
   - Proportion: Balanced and appropriate scale?
   - Texture: Adds value without distraction?
   - Body: Touch targets meet minimums (44x44px or 48x48dp)?
5. **Check Five Pillars**:
   - Purpose: Why does this exist?
   - Craft: Details refined?
   - Constraints: Following system rules?
   - Incompleteness: Room for adaptation?
   - Humans: Accessible and ergonomic?

### After Creating/Modifying a Component

```bash
# Always run both validation commands
npm run validate:tokens
npx tsc --noEmit
```

If either fails, fix before committing.

## When to Surface Issues vs. Handle Internally

### Surface to User:
- **Conflict**: Requirements conflict with design principles
- **Ambiguity**: User input needed to resolve direction
- **Options**: Multiple valid approaches, need preference

### Handle Internally:
- Internal validation checks (just follow protocol)
- Routine token definitions (just add to globals.css)
- Standard accessibility requirements (just implement)

## Common Patterns

### Creating a New Component

```typescript
// 1. Define purpose
// Purpose: Enable users to [specific action] with [specific outcome]

// 2. Define tokens in globals.css first
:root {
  --component-bg: var(--color-surface);
  --component-border: var(--color-border);
  /* ... all variables needed */
}

// 3. Build component with proper structure
export const Component = () => {
  // State (if needed)
  // Accessibility attributes
  // Proper semantic HTML
  // Keyboard navigation
  // Touch targets
  return (/* ... */);
};

// 4. Validate before committing
// npm run validate:tokens && npx tsc --noEmit
```

### Defining Interactions

```typescript
// Motion timing follows protocol
const TIMING = {
  instant: 100,      // Hover states
  responsive: 300,   // Button presses
  deliberate: 500,   // Modals
};

// Easing functions
const EASING = {
  spring: 'cubic-bezier(0.34, 1.56, 0.64, 1)',
  smooth: 'ease-out',
};
```

## Quality Standards

Every component maintains:
- **9.5/10 quality baseline** - Refined, not generic
- **WCAG AA accessibility** - Works for everyone
- **60fps performance** - GPU-accelerated animations
- **Full keyboard support** - Navigate without a mouse
- **Reduced motion support** - Respects user preferences

## Git Workflow

Current branch: `main`
This is a clean repository with recent commits focused on:
- Theme management with ThemeProvider
- Design validation checklists
- Interaction patterns
- Information Architecture
- Discovery Workspace implementation

Follow standard git practices. Always ensure validation passes before committing.

## Technology Stack

- **Framework**: Next.js (React)
- **Language**: TypeScript
- **Styling**: CSS3 with CSS Variables
- **State**: Zustand
- **Icons**: Custom Icon component (24x24 grid, 2px stroke)
- **Fonts**: Sora, Geist Sans, Geist Mono, Source Code Pro

## Amplifier Submodule

This repo includes Amplifier - a separate system for AI-amplified development workflows. It provides knowledge synthesis, parallel exploration, and automation tools that complement Studio's design intelligence.

Located in: `./amplifier/`

## Contributing Philosophy

We welcome contributions that maintain:
- The 9.5/10 quality baseline
- Accessibility standards (WCAG AA minimum)
- Design system consistency
- Purpose-first methodology
- The Five Pillars principles

See `CONTRIBUTING.md` for detailed guidelines.

## Remember

**Quality at creation beats debugging later.**

Every decision compounds:
- Thousands of micro-decisions across nine dimensions
- Each guided by the Five Pillars
- All serving a clear purpose
- Validated against technical standards
- Tested with real humans

**This is what creates 9.5/10 quality.**

Follow the protocol. Run the validators. Ship with confidence.

---

## Quick Reference Card

```
BEFORE ANY WORK:
□ Can articulate WHY in one sentence?
□ All tokens defined in globals.css?
□ Follows 8px spacing system?
□ Meets contrast requirements?
□ Touch targets 44x44px+?
□ Motion timing follows protocol?
□ Keyboard accessible?

AFTER ANY WORK:
□ npm run validate:tokens (passes)
□ npx tsc --noEmit (passes)
□ Component has all states (loading, error, empty, success)
□ Tested reduced motion support
□ Screen reader compatible

SHIP WHEN:
✓ All validations pass
✓ Purpose clearly serves users
✓ Nine dimensions considered
✓ Five pillars embodied
✓ Quality at 9.5/10
```

---

**The artifact is the container. The experience is the product. The values are the legacy. The impact is what matters.**

Design accordingly.
