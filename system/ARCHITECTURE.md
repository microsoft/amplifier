# Amplified Design System - Architecture

**How the meta design system is structured and how products consume it**

---

## The Problem We're Solving

### Without a System (What We Had)
```
studio-interface/
  app/globals.css           ← Design mixed with app code
  components/Icon.tsx       ← App-specific components
```

**Issues:**
- Design improvements stuck in one app
- No reusability across products
- Hard to maintain consistency
- Can't improve "the design" separately from "the app"

### With a System (What We're Building)
```
amplified-design/
  system/                   ← THE DESIGN SYSTEM (source of truth)
  studio-interface/         ← Consumes system
  future-product/           ← Also consumes system
```

**Benefits:**
- Improve system → all products improve
- Consistency by default
- Faster product development
- Meta design feedback targets system, not apps

---

## Architecture Layers

### Layer 1: Foundations (Design Tokens)

**What:** The atomic design decisions (colors, spacing, typography, motion)

**Location:** `system/foundations/`

**Files:**
```
foundations/
  ├── colors.css           ← CSS variables for colors
  ├── typography.css       ← Type scale, fonts
  ├── spacing.css          ← 8px grid
  ├── motion.css           ← Timing, easing, keyframes
  ├── elevation.css        ← Shadows, glassmorphism
  └── tokens.json          ← Exportable design tokens
```

**Example: colors.css**
```css
:root {
  /* Foundation Colors */
  --color-ghost-white: #FAFAFF;
  --color-eerie-black: #1C1C1C;

  /* Semantic Mapping */
  --color-background: var(--color-ghost-white);
  --color-text: var(--color-eerie-black);
}
```

**Used by:** Everything else (components, patterns, products)

---

### Layer 2: Components (Reusable UI)

**What:** Refined, composable UI components

**Location:** `system/components/`

**Structure:**
```
components/
  Button/
    ├── Button.tsx           ← React component
    ├── Button.css           ← Component styles
    ├── Button.stories.tsx   ← Storybook examples
    ├── Button.test.tsx      ← Tests
    └── README.md            ← Usage docs
```

**Example: Button component**
```tsx
// system/components/Button/Button.tsx
import './Button.css'

export type ButtonVariant = 'primary' | 'secondary' | 'ghost'
export type ButtonSize = 'sm' | 'md' | 'lg'

interface ButtonProps {
  variant?: ButtonVariant
  size?: ButtonSize
  children: React.ReactNode
  onClick?: () => void
}

export function Button({
  variant = 'primary',
  size = 'md',
  children,
  onClick
}: ButtonProps) {
  return (
    <button
      className={`amplified-button amplified-button-${variant} amplified-button-${size}`}
      onClick={onClick}
    >
      {children}
    </button>
  )
}
```

**Key Principle:** Components are:
- **Refined** - 9.5/10 quality, not draft quality
- **Accessible** - WCAG AA minimum
- **Composable** - Work together seamlessly
- **Documented** - Clear usage examples

---

### Layer 3: Patterns (Composition Recipes)

**What:** Common ways to combine components

**Location:** `system/patterns/`

**Example: App Layout Pattern**
```tsx
// system/patterns/layouts/AppLayout.tsx
import { Toolbar, Sidebar, Panel } from '@amplified/components'

export function AppLayout({
  toolbar,
  sidebar,
  children
}) {
  return (
    <div className="amplified-app-layout">
      <Toolbar>{toolbar}</Toolbar>
      <div className="amplified-app-body">
        {sidebar && <Sidebar>{sidebar}</Sidebar>}
        <main className="amplified-app-main">
          {children}
        </main>
      </div>
    </div>
  )
}
```

**Used by:** Products to quickly scaffold common UIs

---

### Layer 4: Products (Specific Applications)

**What:** User-facing applications built with the system

**Examples:**
- `studio-interface/` - The design intelligence tool
- Future: `library-app/` - Component library browser
- Future: `docs-site/` - Documentation site

**How they consume the system:**
```tsx
// studio-interface/app/page.tsx
import { Button, Toolbar, Sidebar, Panel } from '@amplified/system'
import '@amplified/system/all.css'

export default function Studio() {
  return (
    <AppLayout
      toolbar={<h1>Studio</h1>}
      sidebar={<ConversationPanel />}
    >
      <Panel>
        <h2>Welcome to Studio</h2>
        <Button variant="primary" size="lg">
          Start New Project
        </Button>
      </Panel>
    </AppLayout>
  )
}
```

---

## Data Flow

### Design Feedback Loop

```
User feedback on Studio Interface
         ↓
Is this a system issue or product issue?
         ↓
    ┌────┴────┐
    │         │
SYSTEM     PRODUCT
issue      issue
    │         │
    ↓         ↓
Fix in     Fix in
system/    studio-interface/
    │         │
    ↓         │
All apps   Only Studio
improve    improves
```

### Examples

**System Issue:**
> "The button hover animation feels sluggish"
- **Fix:** Update `system/foundations/motion.css` timing
- **Impact:** All products get smoother animations

**Product Issue:**
> "Studio should show recent projects on the home screen"
- **Fix:** Add feature to `studio-interface/`
- **Impact:** Only Studio gets this feature

**System Enhancement from Product Need:**
> "Studio needs a dropdown menu, but system doesn't have one"
- **Fix:** Build `system/components/Menu/` with proper motion
- **Impact:** Studio gets the menu, future products can use it too

---

## Motion System Architecture

### Current State (Unrefined)
```css
/* Basic transitions, no choreography */
.studio-button {
  transition: all 200ms ease;
}
```

### Target State (Refined)
```css
/* system/foundations/motion.css */

/* Timing Tokens */
:root {
  --duration-instant: 50ms;
  --duration-responsive: 200ms;
  --duration-deliberate: 400ms;
  --duration-entrance: 300ms;

  --ease-standard: cubic-bezier(0.4, 0, 0.2, 1);
  --ease-spring: cubic-bezier(0.34, 1.56, 0.64, 1);
  --ease-decelerate: cubic-bezier(0.0, 0, 0.2, 1);
}

/* Button Motion */
.amplified-button {
  transition: transform 200ms var(--ease-standard),
              box-shadow 200ms var(--ease-standard);
}

.amplified-button:hover {
  transform: translateY(-1px);
}

.amplified-button:active {
  transform: translateY(0);
  transition-duration: 50ms;
}

/* Menu Motion (Choreographed) */
.amplified-menu {
  animation: menuEnter 200ms var(--ease-decelerate);
}

@keyframes menuEnter {
  from {
    opacity: 0;
    transform: translateY(-8px) scale(0.96);
  }
  to {
    opacity: 1;
    transform: translateY(0) scale(1);
  }
}

/* Menu Items Stagger */
.amplified-menu-item {
  animation: menuItemEnter 150ms var(--ease-decelerate);
  animation-fill-mode: backwards;
}

.amplified-menu-item:nth-child(1) { animation-delay: 0ms; }
.amplified-menu-item:nth-child(2) { animation-delay: 30ms; }
.amplified-menu-item:nth-child(3) { animation-delay: 60ms; }
.amplified-menu-item:nth-child(4) { animation-delay: 90ms; }

@keyframes menuItemEnter {
  from {
    opacity: 0;
    transform: translateX(-4px);
  }
  to {
    opacity: 1;
    transform: translateX(0);
  }
}
```

**Key Improvements:**
1. **Purposeful timing** - Different durations for different contexts
2. **Choreography** - Items animate in sequence, not all at once
3. **Physics-based easing** - Feels natural, not robotic
4. **Performance** - Only animate transform/opacity (GPU-accelerated)

---

## Implementation Strategy

### Phase 1: Extract Foundations (Week 1)
- [ ] Move color system from studio-interface to system/foundations/colors.css
- [ ] Move typography from globals.css to system/foundations/typography.css
- [ ] Move spacing system to system/foundations/spacing.css
- [ ] Create refined motion system in system/foundations/motion.css
- [ ] Extract glassmorphism to system/foundations/elevation.css

### Phase 2: Build Component Library (Week 2)
- [ ] Button component with all variants and refined motion
- [ ] Input component with proper states
- [ ] Panel component with elevation system
- [ ] Menu/Dropdown with choreographed entrance
- [ ] Sidebar with slide animation
- [ ] Toolbar with frosted glass

### Phase 3: Create Patterns (Week 3)
- [ ] AppLayout pattern (toolbar + sidebar + main)
- [ ] Form patterns
- [ ] Navigation patterns
- [ ] Modal patterns

### Phase 4: Migrate Studio Interface (Week 4)
- [ ] Install system package in studio-interface
- [ ] Replace inline styles with system components
- [ ] Remove duplicated CSS
- [ ] Verify no regressions
- [ ] Document integration

### Phase 5: Documentation (Ongoing)
- [ ] Component API documentation
- [ ] Usage examples and recipes
- [ ] Design decision rationale
- [ ] Contribution guidelines

---

## Technical Stack

### System Package
```json
{
  "name": "@amplified/system",
  "version": "0.1.0",
  "type": "module",
  "exports": {
    "./components": "./dist/components/index.js",
    "./foundations": "./dist/foundations/index.css",
    "./all.css": "./dist/all.css"
  }
}
```

### Technologies
- **Components:** React + TypeScript
- **Styling:** CSS with CSS variables (design tokens)
- **Build:** Vite (fast, modern)
- **Docs:** Storybook
- **Testing:** Vitest + Testing Library
- **Package:** npm workspace (monorepo)

### File Organization
```
amplified-design/
  ├── system/                    (Design system package)
  │   ├── package.json
  │   ├── src/
  │   └── dist/                  (Built files)
  │
  ├── studio-interface/          (Consumer app)
  │   ├── package.json
  │   └── node_modules/
  │       └── @amplified/system  (Linked in dev)
  │
  └── package.json               (Root workspace config)
```

---

## Quality Standards

Every system component must meet:

### Design Quality
- [ ] Embodies 9-dimensional framework
- [ ] Refined motion (not generic transitions)
- [ ] Proper accessibility (WCAG AA minimum)
- [ ] Works in all target contexts (desktop, tablet, mobile)

### Code Quality
- [ ] TypeScript with proper types
- [ ] Unit tests with good coverage
- [ ] Storybook examples
- [ ] Documented API and rationale

### Performance
- [ ] No layout thrashing
- [ ] GPU-accelerated animations
- [ ] Code-splittable
- [ ] Small bundle size

---

## Success Metrics

We know the system is working when:

1. **Products improve automatically** - Fix a button in the system, all products get the fix
2. **Faster product development** - New apps can be built quickly by composing system components
3. **Consistent quality** - All products have the same refined aesthetic
4. **Clear feedback loop** - Team knows whether to fix system or product
5. **Documentation works** - New developers can use the system without asking questions

---

## Next Actions

1. **You decide:** Should we extract foundations now or continue refining in studio-interface first?
2. **Motion refinement:** Build the proper choreographed motion system
3. **Component library:** Extract button, input, panel, menu, sidebar, toolbar
4. **Integration:** Migrate studio-interface to consume system

---

**Key Question for You:**

Should we:
- **A)** Continue refining in studio-interface, then extract everything at once
- **B)** Start extracting to system/ now, refine there, migrate studio-interface

What's your preference?
