# Design System Anti-Patterns

This document catalogs common mistakes that violate our design system principles. **These patterns MUST be avoided.**

## 1. Hardcoded Design Values (CRITICAL - HIGH SEVERITY)

**The Problem**: Duplicating CSS variable values in JavaScript/TypeScript code creates multiple sources of truth.

**Why It's Dangerous**:
- Values drift out of sync between CSS and code
- Bugs appear when CSS updates but hardcoded values don't
- Makes theming and dark mode impossible
- Violates Single Source of Truth principle

### The Anti-Pattern (NEVER DO THIS)

```typescript
// ❌ Hardcoded hex colors
const colors = {
  background: '#FAFAFF',
  primary: '#8A8DD0'
};

// ❌ Hardcoded RGB/HSL
const bgColor = 'rgb(250, 250, 255)';
const primary = 'hsl(237, 45%, 69%)';

// ❌ Hardcoded HSL objects (common in color stores)
const DEFAULT_PALETTE = {
  background: { h: 240, s: 1.0, l: 0.99 }  // Duplicates --background!
};

// ❌ Hardcoded spacing
const spacing = { margin: '16px', padding: '24px' };

// ❌ Hardcoded font values
const typography = { fontFamily: 'Sora', fontSize: '14px' };
```

### The Correct Pattern (ALWAYS DO THIS)

```typescript
// ✅ Use CSS variables directly in styles
<div style={{ background: 'var(--background)', padding: 'var(--space-4)' }}>

// ✅ Read CSS variables in TypeScript when needed
import { getCSSVariable } from '@/utils/designTokens';

const background = getCSSVariable('--background');  // '#FAFAFF' (from CSS)
const spacing = getCSSVariable('--space-4');         // '16px' (from CSS)

// ✅ For Tailwind/classes
<div className="bg-background p-4">
```

### How to Detect Violations

**Manual Search**:
```bash
# Find hex colors in TypeScript
grep -r "#[0-9A-Fa-f]\{6\}" --include="*.ts" --include="*.tsx"

# Find rgb/hsl functions
grep -r "rgb\|hsl" --include="*.ts" --include="*.tsx"
```

**Automated**:
```bash
npm run lint:design-tokens  # Will be implemented
```

### How to Fix Existing Violations

1. **Identify** the CSS variable that matches the hardcoded value
2. **Replace** with `var(--variable-name)` in styles
3. **Or use** `getCSSVariable('--variable-name')` in TypeScript
4. **Test** that the values match
5. **Remove** the hardcoded value
6. **Verify** with `npm run validate:tokens`

### Recent Example: colorStore Background Bug

**The Bug**:
```typescript
// colorStore.ts had:
const DEFAULT_PALETTE = {
  background: { h: 220, s: 0.15, l: 0.12 }  // Wrong values!
};

// But globals.css defined:
--background: var(--color-ghost-white);  /* #FAFAFF */
```

**Result**: Background showed as green (#629D5F) instead of ghost white (#FAFAFF).

**The Fix**: Remove DEFAULT_PALETTE or make it read from CSS at runtime.

---

## 2. Other Anti-Patterns (To Be Documented)

- Magic numbers in layout calculations
- Duplicated component logic
- Inconsistent prop naming
- Missing accessibility attributes

---

**Remember**: When you find yourself typing a color, spacing, or font value as a literal, **STOP**. That value should come from `globals.css`.