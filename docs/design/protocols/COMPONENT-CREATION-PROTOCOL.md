# Component Creation Protocol

**Internal validation checklist that MUST be completed before creating or modifying any component**

This protocol ensures every design decision follows FRAMEWORK.md methodology. Run through this mentally before writing code.

---

## Pre-Creation Validation (REQUIRED)

Before creating ANY new component or feature, validate:

### 1. Purpose Validation
- [ ] **Why does this need to exist?** (Can articulate in 1-2 sentences)
- [ ] **What problem does it solve?** (Specific user need identified)
- [ ] **Is this the simplest solution?** (Considered alternatives)

**RED FLAG**: If you can't clearly articulate the "why" in one sentence, STOP and clarify purpose first.

### 2. Design System Audit
- [ ] **All CSS variables will be defined** (Check globals.css before use)
- [ ] **All utility classes will be defined** (No undefined `.studio-*` classes)
- [ ] **Font families are from approved set** (Sora, Geist Sans, Geist Mono, Source Code Pro)
- [ ] **Colors meet WCAG AA** (4.5:1 contrast minimum for text)
- [ ] **Spacing uses 8px system** (4, 8, 12, 16, 24, 32, 48, 64, 96, 128)

**RED FLAG**: If using a new CSS variable, define it in globals.css FIRST, then use it.

### 3. Context Validation
- [ ] **Desktop context considered** (If applicable)
- [ ] **Mobile context considered** (If applicable)
- [ ] **Touch targets sized appropriately** (44x44px minimum if interactive)

**RED FLAG**: If creating interactive elements, ensure touch target size meets requirements.

---

## During Creation (Active Checklist)

### Nine Dimensions Check

For EVERY component, validate these dimensions apply correctly:

#### 1. Style
- [ ] Visual language is consistent with project aesthetic (see `.design/AESTHETIC-GUIDE.md`)
- [ ] No emojis as UI elements (unless project aesthetic explicitly allows)
- [ ] No Unicode characters as icons (use proper Icon component)

#### 2. Motion
- [ ] Timing is appropriate:
  - `<100ms` for hover states (instant feedback)
  - `100-300ms` for button presses (responsive)
  - `300-1000ms` for modals/transitions (deliberate)
  - `>1000ms` has progress indication
- [ ] Easing curve chosen with rationale (ease-out for smooth, spring for energetic)
- [ ] Respects `prefers-reduced-motion`

#### 3. Voice
- [ ] Copy is clear and concise
- [ ] No jargon
- [ ] Error messages are helpful, not blaming
- [ ] Tone adapts to context (serious for errors, friendly for success)

#### 4. Space
- [ ] White space creates hierarchy
- [ ] Proximity shows relationships
- [ ] Layout guides attention
- [ ] Can remove 20% without losing function (simplicity test)

#### 5. Color
- [ ] Contrast ratio validated (4.5:1 minimum for text, 3:1 for UI components)
- [ ] Color choices have documented rationale
- [ ] Cultural context considered

#### 6. Typography
- [ ] Hierarchy is clear (size, weight, color, space)
- [ ] Line height is 1.125-1.5× font size
- [ ] Maximum 2-3 typefaces used

#### 7. Proportion
- [ ] Scale relationships feel balanced
- [ ] Visual adjustment applied where needed

#### 8. Texture
- [ ] Texture serves purpose (not decoration)
- [ ] Doesn't reduce readability

#### 9. Body (Ergonomics)
- [ ] Touch targets are 44×44px minimum (Apple) or 48×48dp (Android)
- [ ] Thumb zones considered for mobile
- [ ] Keyboard navigation works

---

## Five Pillars Check (Quick Validation)

Before finalizing any component:

### 1. Purpose Drives Execution ✓
- Can explain WHY this variant/approach was chosen (not just "looks good")

### 2. Craft Embeds Care ✓
- Edge cases handled (error, loading, empty states)
- Details refined (timing, spacing, contrast)
- No arbitrary values

### 3. Constraints Enable Creativity ✓
- Works within design system
- Locked properties respected
- Found creativity within constraints

### 4. Intentional Incompleteness ✓
- Room for user expression
- Content customizable
- Not over-engineered

### 5. Design for Humans ✓
- Keyboard navigable
- Screen reader compatible
- Color contrast validated
- Touch targets sized appropriately

---

## Post-Creation Validation (AUTOMATED)

After writing code, run these validators:

### 1. CSS Variable Validation
```bash
npm run validate:tokens
```
**MUST PASS** - No undefined CSS variables allowed

### 2. TypeScript Compilation
```bash
npx tsc --noEmit
```
**MUST PASS** - No type errors allowed

### 3. Build Validation
```bash
npm run build
```
**MUST PASS** - Production build must succeed

---

## Decision Flow

```
┌─────────────────────────────────────┐
│ New Component/Feature Requested     │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 1. Can I articulate WHY in 1 sent?  │
│    ├─ NO  → STOP, clarify first     │
│    └─ YES → Continue                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 2. Are all design tokens defined?   │
│    ├─ NO  → Define in globals.css   │
│    └─ YES → Continue                │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 3. Run through 9 dimensions         │
│    (Style, Motion, Voice, Space,    │
│     Color, Typography, Proportion,  │
│     Texture, Body)                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 4. Verify Five Pillars alignment    │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 5. Write code                       │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 6. Run automated validators         │
│    - npm run validate:tokens        │
│    - npx tsc --noEmit               │
│    - npm run build                  │
└──────────────┬──────────────────────┘
               │
               ▼
┌─────────────────────────────────────┐
│ 7. All pass? Ship it.               │
│    Not pass? Fix before proceeding  │
└─────────────────────────────────────┘
```

---

## Common Violations to Watch For

### ❌ ANTI-PATTERNS

1. **Using undefined CSS variables**
   ```tsx
   // ❌ BAD
   style={{ color: 'var(--new-color)' }}

   // ✅ GOOD
   // First add to globals.css:
   // --new-color: hsl(217, 90%, 60%);
   // Then use:
   style={{ color: 'var(--new-color)' }}
   ```

2. **Emojis as UI elements**
   ```tsx
   // ❌ BAD
   <button>⚙️</button>

   // ✅ GOOD
   <button><SettingsIcon size={18} /></button>
   ```

3. **Arbitrary spacing values**
   ```tsx
   // ❌ BAD
   style={{ padding: '17px' }}

   // ✅ GOOD
   style={{ padding: 'var(--space-4)' }} // 16px from 8px system
   ```

4. **Poor contrast ratios**
   ```tsx
   // ❌ BAD
   style={{ color: '#999', background: '#ddd' }} // 2.3:1 contrast

   // ✅ GOOD
   style={{ color: 'var(--text)', background: 'var(--background)' }} // 4.5:1+
   ```

5. **Missing touch targets**
   ```tsx
   // ❌ BAD
   <button style={{ width: '24px', height: '24px' }}>×</button>

   // ✅ GOOD
   <button className="studio-button-icon"> {/* 36x36px minimum */}
     <CloseIcon size={18} />
   </button>
   ```

6. **No keyboard support**
   ```tsx
   // ❌ BAD
   <div onClick={handleClick}>Click me</div>

   // ✅ GOOD
   <button onClick={handleClick}>Click me</button>
   // OR
   <div onClick={handleClick} onKeyDown={handleKeyDown} tabIndex={0} role="button">
     Click me
   </div>
   ```

7. **Missing loading/error/empty states**
   ```tsx
   // ❌ BAD
   return <div>{data.map(item => <Item key={item.id} {...item} />)}</div>

   // ✅ GOOD
   if (loading) return <LoadingState />
   if (error) return <ErrorState message={error.message} />
   if (data.length === 0) return <EmptyState />
   return <div>{data.map(item => <Item key={item.id} {...item} />)}</div>
   ```

---

## Integration with AI Workflow

**For Claude/AI Assistant:**

Before creating any component, internally run through this checklist. If any check fails:
1. **STOP** - Do not proceed with code generation
2. **FIX** - Address the issue (define variable, adjust contrast, etc.)
3. **VALIDATE** - Confirm fix meets requirements
4. **PROCEED** - Continue with code generation

**The user should never see this checklist in conversation** - it's an internal validation protocol. Only surface issues to the user if:
- There's a conflict between requirements and design principles
- User input is needed to resolve ambiguity
- Multiple valid approaches exist and user preference is needed

---

## Validation Frequency

- **Every new component**: Full protocol
- **Every component modification**: Relevant sections (e.g., if changing colors, re-validate color contrast)
- **Before committing**: Run all automated validators
- **Weekly audit**: Run `npm run validate:tokens` on entire codebase

---

## Automated Pre-Commit Hook (TODO)

Future: Create git pre-commit hook that runs:
```bash
#!/bin/bash
# .git/hooks/pre-commit

echo "Running design token validation..."
npm run validate:tokens || exit 1

echo "Running TypeScript check..."
npx tsc --noEmit || exit 1

echo "All checks passed!"
exit 0
```

---

## Success Metrics

**How to know this protocol is working:**

1. ✅ Zero undefined CSS variables in production
2. ✅ All interactive elements have proper touch targets
3. ✅ All text meets WCAG AA contrast requirements
4. ✅ All components have loading/error/empty states
5. ✅ Build succeeds on first try (no compilation errors)
6. ✅ No emergency fixes needed post-deployment

---

## Remember

**This protocol exists to ensure quality, not to slow down development.**

The checklist becomes second nature with practice. Initially it may feel like overhead, but it prevents:
- Undefined CSS variable bugs
- Accessibility issues
- Inconsistent design system application
- Missing edge case handling
- Emergency hotfixes

**Quality at creation beats debugging later.**
