# Amplified Design System

**The meta design system that powers all Amplified products**

This is the design system that embodies our 9-dimensional framework. When you improve this system, all products built with it improve automatically.

---

## What Is This?

**Amplified Design System** is the reusable, refined component library and design foundation that implements our design philosophy:

- 9-dimensional design framework
- German car facility aesthetic (clean, precise, beautiful)
- 9.5/10 quality through subtle refinement
- Purpose-driven execution

---

## Structure

```
system/
├── foundations/          Design tokens and base styles
│   ├── colors.css       Color palette and semantic colors
│   ├── typography.css   Type scale, fonts, hierarchy
│   ├── spacing.css      8px grid system
│   ├── motion.css       Timing, easing, animations
│   └── elevation.css    Glassmorphism and shadows
│
├── components/          Reusable UI components
│   ├── Button/          All button variants
│   ├── Input/           Form inputs
│   ├── Panel/           Containers with elevation
│   ├── Menu/            Dropdowns and menus
│   ├── Sidebar/         Collapsible sidebars
│   └── Toolbar/         Top navigation bars
│
├── patterns/            Composition patterns
│   ├── layouts/         Common layout patterns
│   ├── navigation/      Nav patterns
│   └── forms/           Form patterns
│
└── tokens.json          Design tokens (for export)
```

---

## Philosophy: Meta Design vs. Product Design

### This is META design
- **What:** The design system itself
- **Purpose:** Reusable foundations and components
- **Changes here:** Affect all products that use the system
- **Quality bar:** 9.5/10 - extremely refined

### Product design (e.g., studio-interface)
- **What:** Specific applications built with the system
- **Purpose:** User-facing features and flows
- **Changes here:** Only affect that product
- **Quality bar:** Inherits from system + product-specific refinement

---

## How Products Use This System

### Example: Studio Interface

```tsx
// studio-interface imports from system/
import { Button, Panel, Toolbar } from '@amplified/system/components'
import '@amplified/system/foundations/all.css'

// Studio just composes system components
export default function Studio() {
  return (
    <Toolbar>
      <Button variant="primary">Start Project</Button>
    </Toolbar>
  )
}
```

When you improve `Button` in the system, Studio (and all other apps) get the improvement automatically.

---

## Design Principles

From [FRAMEWORK.md](../FRAMEWORK.md) and [PRINCIPLES.md](../PRINCIPLES.md):

### The Five Pillars
1. **Purpose Drives Execution** - Every component exists for a reason
2. **Craft Embeds Care** - Details show respect
3. **Constraints Enable Creativity** - Structure unlocks solutions
4. **Intentional Incompleteness** - Leave room for product context
5. **Design for Humans** - Accessibility is non-negotiable

### The Nine Dimensions
1. **Style** - Visual language (German car facility aesthetic)
2. **Behaviors** - Motion timing and interaction patterns
3. **Voice** - Language personality (confident simplicity)
4. **Space** - Layout and hierarchy (8px grid)
5. **Color** - Meaning and function (foundation + semantic)
6. **Typography** - Hierarchy and legibility (Sora + Geist)
7. **Proportion** - Scale and balance (44px touch targets)
8. **Texture** - Materiality and depth (glassmorphism)
9. **Body** - Ergonomics and accessibility (WCAG AA)

---

## Current Status

**Phase:** Foundation establishment
**Products using this system:**
- Studio Interface (in progress)

**Next steps:**
1. Extract refined foundations from studio-interface
2. Build component library with proper motion
3. Create documentation and examples
4. Publish as npm package (future)

---

## Contributing

When adding or improving system components:

1. **Follow the 9 dimensions** - Every change should be evaluated across all dimensions
2. **Maintain quality bar** - 9.5/10 is the standard
3. **Document rationale** - Explain why, not just what
4. **Test accessibility** - WCAG AA minimum
5. **Consider all contexts** - Desktop, tablet, mobile, keyboard, screen reader

---

## References

- [FRAMEWORK.md](../FRAMEWORK.md) - 9-dimensional framework
- [PRINCIPLES.md](../PRINCIPLES.md) - Five pillars
- [PHILOSOPHY.md](../PHILOSOPHY.md) - Deep philosophy
- [studio-interface/IMPLEMENTATION-SPEC.md](../studio-interface/IMPLEMENTATION-SPEC.md) - First implementation

---

**Remember:** This is the design system that Studio uses to guide users through design decisions. It must embody the quality we're helping users achieve.
