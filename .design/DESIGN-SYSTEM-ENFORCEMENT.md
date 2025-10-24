# Design System Enforcement Protocol

## Core Principle
**NO HARDCODED VALUES. EVER.**

If a value appears more than once, it's a token.
If a value relates to color, spacing, typography, shadow, or interaction - it's a token.
If you're tempted to write `#FF0000` or `rgba(...)` - STOP. Use a token.

---

## The Problem (2025-10-15)

During dark mode audit, found **56+ hardcoded color values** in components:
- `rgba(218, 221, 216, 0.4)` instead of `var(--border)`
- `rgba(138, 141, 208, 0.08)` instead of `var(--color-hover-accent)`
- `rgba(28, 28, 28, 0.04)` instead of `var(--color-hover)`
- White backgrounds hardcoded: `rgba(255, 255, 255, 0.85)`

**Result:** Dark mode was broken. Light mode worked by accident.

---

## Design System Token Hierarchy

### 1. Foundation Tokens (Never Use Directly in Components)
```css
/* These are ONLY for defining semantic tokens */
--color-ghost-white
--color-anti-flash-white
--color-alabaster
--color-platinum
--color-eerie-black
```

### 2. Semantic Tokens (Always Use These)
```css
/* Backgrounds */
--background          /* Canvas, page background */
--bg-primary          /* Primary surface */
--bg-secondary        /* Elevated surface */
--surface             /* Panel surface */
--surface-warm        /* Warm-toned surface */
--surface-muted       /* Subtle surface */

/* Text */
--text                /* Primary text */
--text-primary        /* Same as --text */
--text-muted          /* Secondary text (WCAG AA) */

/* Borders */
--border              /* Default borders */
--border-default      /* Same as --border */

/* Interactive States */
--color-hover         /* Hover state overlay */
--color-active        /* Active/pressed state */
--color-focus         /* Focus ring */

/* Brand Colors */
--primary             /* Primary brand color */
--accent              /* Accent brand color */

/* Feedback */
--color-success       /* Success states */
--color-attention     /* Warning states */
--color-error         /* Error states */

/* Shadows */
--shadow-sm           /* Small shadow */
--shadow-md           /* Medium shadow */
--shadow-lg           /* Large shadow */
--shadow-elevated     /* Elevated panels */
--shadow-modal        /* Modal overlays */

/* Spacing */
--space-1 through --space-32
```

---

## Enforcement Rules

### Rule 1: CSS Files
❌ **NEVER:**
```css
.my-component {
  background: #FFFFFF;
  color: rgba(28, 28, 28, 0.8);
  border: 1px solid #DADDD8;
}
```

✅ **ALWAYS:**
```css
.my-component {
  background: var(--bg-primary);
  color: var(--text);
  border: 1px solid var(--border);
}
```

### Rule 2: React/TSX Files
❌ **NEVER:**
```tsx
<div style={{
  backgroundColor: '#F8F9F6',
  color: '#1C1C1C',
  padding: '16px',
  border: '1px solid rgba(218, 221, 216, 0.4)'
}}>
```

✅ **ALWAYS:**
```tsx
<div style={{
  backgroundColor: 'var(--bg-primary)',
  color: 'var(--text)',
  padding: 'var(--space-4)',
  border: '1px solid var(--border)'
}}>
```

### Rule 3: Component Props
When a component needs custom colors (e.g., accent color for theming):

❌ **NEVER:**
```tsx
<ChatPanel accentColor="#8A8DD0" />
```

✅ **ALWAYS:**
```tsx
// In component
const accentColor = 'var(--accent)'

<ChatPanel accentColor={accentColor} />
```

### Rule 4: Dynamic Values
For generated/dynamic colors (like palette systems):

✅ **ACCEPTABLE:**
```tsx
// Predefined palettes are OK
const PALETTES = [
  { bg: '#F8F9F6', accent: '#1C1C1C' }, // These are data, not styles
]

// But still reference tokens when applying:
<div style={{
  backgroundColor: currentPalette.bg,  // OK - using palette data
  border: `1px solid var(--border)`     // Still use token for border
}}>
```

---

## Token Usage Guide

### Colors

| Use Case | Token | Example |
|----------|-------|---------|
| Page background | `var(--background)` | Main app canvas |
| Panel background | `var(--bg-secondary)` | Floating chat panel |
| Modal background | `var(--bg-primary)` | Auth modal |
| Text primary | `var(--text)` | Headings, body text |
| Text secondary | `var(--text-muted)` | Captions, metadata |
| Border | `var(--border)` | All borders |
| Hover overlay | `var(--color-hover)` | Button hover |
| Active overlay | `var(--color-active)` | Button pressed |
| Focus ring | `var(--color-focus)` | Keyboard focus |

### Spacing

| Use Case | Token | Value |
|----------|-------|-------|
| Tiny gap | `var(--space-1)` | 4px |
| Small gap | `var(--space-2)` | 8px |
| Medium gap | `var(--space-4)` | 16px |
| Large gap | `var(--space-6)` | 24px |
| Section gap | `var(--space-8)` | 32px |
| Major section | `var(--space-12)` | 48px |

### Shadows

| Use Case | Token |
|----------|-------|
| Small elements | `var(--shadow-sm)` |
| Buttons | `var(--shadow-md)` |
| Panels | `var(--shadow-elevated)` |
| Modals | `var(--shadow-modal)` |

---

## Pre-Implementation Checklist

Before writing ANY new component:

- [ ] I have reviewed the design system tokens in `globals.css`
- [ ] I know which tokens I'll use for backgrounds
- [ ] I know which tokens I'll use for text colors
- [ ] I know which tokens I'll use for borders
- [ ] I know which tokens I'll use for interactive states
- [ ] I will NOT hardcode any hex colors
- [ ] I will NOT hardcode any rgba() values
- [ ] I will NOT hardcode any spacing values (use --space-*)

---

## Code Review Checklist

When reviewing any PR:

- [ ] No hardcoded hex colors (#XXXXXX)
- [ ] No hardcoded rgb/rgba values (except in CSS variable definitions)
- [ ] All colors use var(--token-name)
- [ ] All spacing uses var(--space-N)
- [ ] All shadows use var(--shadow-name)
- [ ] Interactive states use var(--color-hover/active/focus)
- [ ] Component will work in BOTH light AND dark mode

---

## Automated Enforcement

### ESLint Rule (Future)
```js
// Detect hardcoded colors in TSX
'no-hardcoded-colors': {
  pattern: /(#[0-9A-Fa-f]{3,6}|rgba?\()/,
  message: 'Use design system tokens instead of hardcoded colors'
}
```

### Git Pre-commit Hook (Future)
```bash
# Check for hardcoded values
if grep -r "#[0-9A-Fa-f]\{6\}\|rgba\|rgb" components/ | grep -v "var(--"; then
  echo "ERROR: Hardcoded colors detected. Use design system tokens."
  exit 1
fi
```

---

## Migration Strategy

For existing components with hardcoded values:

### 1. Identify
```bash
grep -r "rgba\|#[0-9A-Fa-f]" components/ | grep -v "var(--"
```

### 2. Map to Tokens
```
rgba(218, 221, 216, 0.4) → var(--border)
rgba(28, 28, 28, 0.04)   → var(--color-hover)
rgba(138, 141, 208, 0.08) → var(--color-hover-accent) [ADD TOKEN]
#1C1C1C                   → var(--text) in light, var(--background) in dark
```

### 3. Replace Systematically
Work file by file, test in BOTH light and dark mode.

### 4. Add Missing Tokens
If you need a value not in the system:
1. Add it to `globals.css` with light + dark definitions
2. Document it in this guide
3. Use it consistently

---

## Adding New Tokens

When adding a new semantic token:

### 1. Define in Light Mode
```css
:root {
  --new-token-name: value; /* Light mode value */
}
```

### 2. Define in Dark Mode
```css
@media (prefers-color-scheme: dark) {
  :root {
    --new-token-name: value; /* Dark mode value */
  }
}

[data-theme="dark"] {
  --new-token-name: value; /* Manual dark mode */
}
```

### 3. Document Here
Add to the semantic tokens table above.

### 4. Use Consistently
Never hardcode the value again. Always reference the token.

---

## Common Mistakes & Fixes

### Mistake 1: "I need a custom color for this one component"
**Wrong approach:** Hardcode it
**Right approach:** Add a semantic token

### Mistake 2: "The token doesn't match my design exactly"
**Wrong approach:** Hardcode the exact value
**Right approach:** Either:
- Use the closest token (maintain consistency)
- Add a new semantic token if it's a system-wide pattern
- Adjust the token if this is the correct value

### Mistake 3: "I'm just prototyping"
**Wrong approach:** "I'll fix it later" (you won't)
**Right approach:** Use tokens from the start. It's actually faster.

### Mistake 4: "Dark mode doesn't work"
**Root cause:** You hardcoded values
**Fix:** Use tokens. They adapt automatically.

---

## Success Metrics

### We're succeeding when:
- Dark mode works perfectly without additional changes
- New components automatically support theme switching
- Designers can change brand colors by editing 2 lines
- Zero hardcoded colors found in `grep` audit
- Contributors naturally reach for tokens first

### We're failing when:
- Dark mode breaks with new components
- Theme changes require editing 50+ files
- `grep` finds hardcoded values
- Contributors ask "which token should I use?"

---

## Philosophy

Design systems exist to create **systematic consistency**. Every hardcoded value is a failure of the system.

The goal isn't to have tokens - it's to have a system where decisions are made once, globally, and applied everywhere automatically.

**Truth is action.** If we say we have a design system but use hardcoded values, we don't have a design system. We have scattered CSS.

---

Last updated: 2025-10-15
After dark mode audit revealed 56+ violations
