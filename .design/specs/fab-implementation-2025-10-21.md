---
feature: FloatingChatFAB
date: 2025-10-21
status: implemented
project: studio-interface
tags: [fab, chat, interaction, motion, turbopack-inspired]
supersedes: null
related: [FAB-TURBOPACK-ANALYSIS.md, FAB-VISUAL-REFERENCE.md, FAB-DECISION-RATIONALE.md]
---

# FloatingChatFAB Implementation Spec

**Status**: implemented
**Project**: studio-interface
**Date**: 2025-10-21
**Agent**: zen-architect

---

## Purpose & Context

**Why this exists**: Provide draggable chat access with premium material sophistication

**Problem solved**: Generic FAB interactions lack the tactile, refined quality users expect from premium tools

**Emotional goal**: Premium feel with user agency - Turbopack-level visual sophistication combined with superior draggable UX

**Related decisions**: Hybrid approach - keep draggable functionality, adopt Turbopack visual refinement

---

## Design Decisions

### Aesthetic Brief
- **Style**: Turbopack-inspired material sophistication with blur + transparency
- **Motion**: Faster response (150ms hover), subtler scale (1.03), new press feedback (0.97)
- **Voice**: Premium tool that respects user control
- **Space**: Tighter 20px padding (refined positioning)
- **Color**: Material with 0.92 alpha for depth, supports light/dark themes
- **Typography**: N/A (icon-only)
- **Proportion**: 7% smaller (52px vs 56px), larger icon (28px vs 24px)
- **Texture**: Four-layer shadow system for material depth
- **Body**: 52px exceeds 44px minimum touch target

### Key Constraints
- Maintain draggable functionality (user agency non-negotiable)
- GPU-accelerated animations only (60fps requirement)
- Must work in light and dark themes
- Preserve spring physics and corner snapping
- Position persistence in localStorage

---

## Implementation Requirements

### Modules to Create/Modify
- `studio-interface/components/FloatingChatFAB.tsx` - Update constants (FAB_SIZE, FAB_PADDING)
- `studio-interface/components/chat/FABButton.tsx` - Complete refinement with state handling
- `studio-interface/app/globals.css` - Add comprehensive FAB token system

### CSS Variables Required
Define in `studio-interface/app/globals.css`:
```css
/* FAB System */
--fab-size: 52px;
--fab-icon-size: 28px;
--fab-padding-mobile: 16px;
--fab-padding-desktop: 20px;

/* Material */
--fab-bg: rgba(28, 28, 28, 0.92);
--fab-bg-hover: rgba(28, 28, 28, 0.96);
--fab-color: rgba(255, 255, 255, 0.98);
--fab-backdrop: blur(32px) saturate(140%);

/* Shadows (4-layer system) */
--fab-shadow-default:
  0 0 0 1px rgba(28, 28, 28, 0.12),
  inset 0 1px 0 0 rgba(255, 255, 255, 0.08),
  0 2px 8px -2px rgba(28, 28, 28, 0.12),
  0 12px 32px -8px rgba(28, 28, 28, 0.16);

--fab-shadow-hover:
  0 0 0 1px rgba(28, 28, 28, 0.14),
  inset 0 1px 0 0 rgba(255, 255, 255, 0.10),
  0 4px 12px -2px rgba(28, 28, 28, 0.14),
  0 16px 48px -8px rgba(28, 28, 28, 0.20);

--fab-shadow-active:
  0 0 0 1px rgba(28, 28, 28, 0.14),
  inset 0 1px 0 0 rgba(255, 255, 255, 0.06),
  0 1px 4px -1px rgba(28, 28, 28, 0.16),
  0 4px 16px -4px rgba(28, 28, 28, 0.24);

--fab-shadow-dragging: var(--shadow-modal);

/* Motion */
--fab-scale-default: 1;
--fab-scale-hover: 1.03;
--fab-scale-active: 0.97;
--fab-duration-hover: 150ms;
--fab-duration-state: 250ms;
--fab-ease-hover: cubic-bezier(0.23, 0.88, 0.26, 0.92);
```

### Success Criteria
- [x] Functional: Dragging, snapping, spring physics maintained
- [x] Aesthetic: Turbopack-level material sophistication
- [x] Accessibility: 52px exceeds 44px minimum
- [x] Performance: GPU-accelerated (transform + opacity)
- [x] Keyboard: N/A (draggable interaction primary)
- [x] Touch: 52px touch target with grab cursor

---

## Rationale

**Why these choices**:
- **Purpose**: User agency (dragging) + premium quality (Turbopack visual)
- **Craft**: Four-layer shadows, backdrop blur, precise timing
- **Constraints**: 8px system (52px = 6.5 × 8px), GPU-only animations
- **Incompleteness**: Future notification badge, keyboard controls
- **Humans**: 52px touch target, grab cursor, tactile press feedback

**Alternatives considered**:
- Static positioning (rejected - removes user agency)
- Panel-only chat (rejected - always-on access better)
- Keyboard-first (future enhancement - drag primary for spatial control)

**References**:
- Turbopack FAB (material quality)
- Framer Motion (spring physics)
- Apple HIG (touch targets, motion timing)

---

## Nine Dimensions Evaluation

- **Style**: Turbopack-inspired blur + transparency material
- **Motion**: 150ms hover (responsive), 100ms active (instant feedback), spring on release
- **Voice**: "Premium tool, user control" - tactile, refined, respectful
- **Space**: Tighter 20px padding (intentional positioning)
- **Color**: Material alpha (0.92) with theme support
- **Typography**: N/A (icon-only interface)
- **Proportion**: 7% smaller FAB (refined), 17% larger icon (presence)
- **Texture**: Four-layer shadow system (border, highlight, near, far)
- **Body**: 52px exceeds Apple 44px guideline, grab cursor for affordance

---

## Five Pillars Check

1. **Purpose Drives Execution**: Always-on chat access with spatial control (draggable)
2. **Craft Embeds Care**: Four shadow layers, backdrop blur saturation, precise easing curves
3. **Constraints Enable Creativity**: 52px respects 8px system while exceeding touch targets
4. **Intentional Incompleteness**: Future notification badge, keyboard controls, message count
5. **Design for Humans**: Tactile press feedback (0.97 scale), grab cursor, spring physics feel natural

---

## Validation

```bash
# Run before committing
npm run validate:tokens  # CSS variables check
npx tsc --noEmit        # TypeScript check
npm run build           # Production build
```

All must pass.

---

## Testing Checklist

- [x] FAB appears at correct size (52px)
- [x] FAB positioned with 20px padding
- [x] Icon is 28px and properly centered
- [x] Hover scales to 1.03 in 150ms
- [x] Active/press scales to 0.97 in 100ms
- [x] Dragging maintains scale at 1.0
- [x] Shadow transitions smoothly (4 layers visible)
- [x] Backdrop blur applies correctly
- [x] Works in light mode
- [x] Works in dark mode
- [x] Spring physics still works on release
- [x] Corner snapping still works
- [x] Position persists in localStorage

---

## Future Enhancements (Phase 2)

- Notification badge with actual message count
- Attention pulse animation on new messages
- Keyboard controls (arrow keys for positioning)
- Accessibility: Announce position changes to screen readers
