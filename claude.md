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

## Critical Protocols: The Foundation

**BEFORE creating or modifying ANY component, you MUST:**

1. **Check the Aesthetic Guide** → `.design/AESTHETIC-GUIDE.md`
   - Establish emotional tone first
   - Reference color palettes, interactions, timing
   - Ensure Swedish design studio vibe (not corporate)

2. **Validate Component Standards** → `.design/COMPONENT-CREATION-PROTOCOL.md`
   - Technical implementation requirements

### Non-Negotiable Requirements

1. **CSS Variables**: All variables MUST be defined in `studio-interface/app/globals.css` BEFORE use
   - Run `npm run validate:tokens` after any changes
   - Zero undefined variables allowed in production

2. **Design System Compliance**:
   - Spacing: 8px system only (4, 8, 12, 16, 24, 32, 48, 64, 96, 128)
   - Fonts: Sora (headings), Geist Sans (body), Geist Mono (code)
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

6. **No Hardcoded Design Values (CRITICAL)**:
   **The Single Source of Truth Rule**: ALL design values MUST come from CSS variables in `globals.css`.

   **NEVER hardcode:**
   - ❌ Colors: `#FAFAFF`, `rgb(250, 250, 255)`, `hsl(240, 100%, 99%)`, `{ h: 240, s: 1, l: 0.99 }`
   - ❌ Spacing: `16px`, `1rem`, specific pixel values
   - ❌ Typography: Font names, sizes as literals
   - ❌ Shadows, borders, radii: Any literal CSS values

   **ALWAYS use CSS variables:**
   ```typescript
   // ❌ WRONG - Hardcoded
   const bg = '#FAFAFF';
   const spacing = { padding: '16px' };

   // ✅ RIGHT - CSS variables
   const bg = 'var(--background)';
   const spacing = { padding: 'var(--space-4)' };
   ```

   **For React components** needing values in TypeScript:
   ```typescript
   import { getCSSVariable } from '@/utils/designTokens';

   const bgColor = getCSSVariable('--background');  // Reads at runtime
   ```

   **For stores/state initialization**:
   Never set hardcoded defaults. Read from CSS at runtime or use CSS variables directly in styles.

   **When You MUST Use a Literal** (rare):
   ```typescript
   // TODO: Remove when library supports CSS vars
   // Required by ThirdPartyLib - must match --background
   const CHART_BG = '#FAFAFF';
   ```

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
├── .claude/                   # Project-specific Claude Code agents
│   ├── agents/
│   │   ├── animation-choreographer.md  # Motion design specialist
│   │   ├── component-designer.md       # Component design specialist
│   │   └── design-system-architect.md  # System architecture specialist
│   ├── commands/
│   │   └── designer.md        # /designer slash command
│   └── README.md              # Agent documentation
├── ai_working/                # Studio-specific AI tool workspace
│   ├── discovery_processor/  # Process content for Discovery canvas
│   ├── tmp/                  # Temporary files (gitignored)
│   └── README.md             # AI tools documentation
├── studio-interface/          # Next.js app - main Studio interface
│   ├── app/
│   │   ├── globals.css       # ALL CSS variables defined here
│   │   └── ...
│   ├── components/
│   │   └── icons/Icon.tsx    # Icon system (24x24 grid, 2px stroke)
│   ├── state/store.ts        # Zustand global state
│   └── ...
├── amplifier/                 # Amplifier submodule (general-purpose)
│   ├── .claude/
│   │   ├── agents/           # zen-architect, modular-builder, bug-hunter, etc.
│   │   └── commands/         # General-purpose commands
│   └── ai_working/           # Amplifier AI tools (general-purpose)
├── packages/                  # Modular packages
│   └── interactions/         # Common interaction patterns
├── components/               # Design components library
├── agents/                   # Legacy - being migrated to .claude/agents/
├── quality-guardrails/       # Validation rules
├── knowledge-base/           # Design theory documentation
├── .design/                  # Design documentation and checklists
│   ├── specs/                # Agent-generated design specifications
│   └── COMPONENT-CREATION-PROTOCOL.md
├── FRAMEWORK.md             # Complete design sensibility framework
├── PHILOSOPHY.md            # Five Pillars deep dive
├── PRINCIPLES.md            # Quick reference guide
├── VISION.md                # Beyond the artifact philosophy
└── README.md                # Project overview
```

## Design Specification Infrastructure

**Agent-generated specs with persistent storage, discovery, and context-aware regeneration.**

### Overview

Design specifications are:
- **Agent-generated** (dynamic, context-aware)
- **Persisted** (saved for reference and discovery)
- **Versioned** (linked via metadata)
- **Discoverable** (via indexes and semantic search)

**Philosophy**: Specs are living documents that agents regenerate with fresh context while preserving decision history.

### Creating Specifications

When generating design specs (via ux-wireframe-designer or design-diagnostics):

**1. Discover related work FIRST**:
```bash
# Search for related specs
grep -r "feature-keyword" .design/specs/
grep -l "tags:.*animation" .design/specs/*.md
```

Present findings to user: "I found [X] related specs. Should I reference these?"

**2. Generate spec following template**:
- Use `.design/specs/TEMPLATE.md` as structure reference
- Include all sections: Purpose, Design Decisions, Implementation, Rationale
- Apply Nine Dimensions + Five Pillars evaluation

**3. Save with metadata**:
```markdown
---
feature: [FeatureName]
date: YYYY-MM-DD
status: planned | in-progress | implemented
project: studio-interface | components | system
tags: [descriptive, searchable, tags]
supersedes: null | previous-spec.md
related: [related-spec-1.md]
---
```

**4. Save location**: `.design/specs/[feature-name]-[YYYY-MM-DD].md`

**5. Regenerate index**: `.design/scripts/generate-specs-index.sh`

**6. Notify user**: "Saved to .design/specs/[filename]"

### Finding Specifications

**Via Index**:
- Master index: `INDEX.md` (root level)
- Specs index: `.design/specs/INDEX.md`

**Via Search**:
```bash
# Find by feature name
grep -r "feature-keyword" .design/specs/

# Find by tag
grep -l "tags:.*animation" .design/specs/*.md

# Find active work
ls .design/active/ACTIVE-*.md

# Find recent specs (last 30 days)
find .design/specs -name "*.md" -mtime -30
```

**Example Searches**:
```bash
# Find all specs about animations or motion
grep -l "tags:.*motion\|animation" .design/specs/*.md

# Find all in-progress work
grep -l "status: in-progress" .design/specs/*.md

# Find specs mentioning FloatingChatFAB
grep -r "FloatingChatFAB\|FAB\|floating action" .design/specs/

# Find specs that reference canvas features
grep -r "canvas\|toolbar" .design/specs/

# Find specs from October 2025
ls .design/specs/*-2025-10-*.md

# Find specs that supersede other specs (version chains)
grep -l "supersedes:" .design/specs/*.md
```

### Regenerating Specifications

When updating an existing spec:

**1. Read original spec** from `.design/specs/[feature]-[old-date].md`

**2. Extract context**:
- Original decisions and rationale
- Constraints established
- Related specs referenced

**3. Generate new spec** with updated requirements

**4. Link versions via metadata**:
```yaml
# New spec
supersedes: [feature]-[old-date].md

# Old spec (update its metadata)
superseded-by: [feature]-[new-date].md
status: superseded
```

**5. Include changes section**:
```markdown
## Changes from Previous Spec

**Previous**: [feature]-[old-date].md

**Key changes**:
- [Change 1]: [Rationale]
- [Change 2]: [Rationale]
```

### Spec Lifecycle

**Statuses**:
- `planned`: Not yet started
- `in-progress`: Currently being implemented
- `implemented`: Complete and shipped
- `superseded`: Replaced by newer version

**Version Chain Example**:
```
fab-implementation-2025-10-15.md (superseded)
  ↓ superseded-by
fab-implementation-2025-10-21.md (implemented)
```

### Directory Structure

```
.design/
├── specs/                          # Persistent agent-generated specs
│   ├── INDEX.md                    # Auto-generated catalog
│   ├── TEMPLATE.md                 # Spec structure reference
│   ├── fab-implementation-2025-10-21.md
│   ├── canvas-toolbar-2025-10-18.md
│   └── [feature]-[YYYY-MM-DD].md
│
├── active/                         # Current work
│   ├── ACTIVE-studio-discovery.md
│   ├── TODO-typography-system.md
│   └── BLOCKED-feature-name.md
│
├── scripts/                        # Auto-generation
│   ├── generate-specs-index.sh     # Regenerate specs/INDEX.md
│   └── generate-master-index.sh    # Regenerate root INDEX.md
│
└── [protocols...]                  # COMPONENT-CREATION-PROTOCOL.md, etc.
```

### Best Practices

**DO**:
- ✅ Search for related specs before generating new ones
- ✅ Reference past decisions with rationale for changes
- ✅ Include comprehensive metadata (tags, related specs)
- ✅ Follow TEMPLATE.md structure
- ✅ Apply Nine Dimensions + Five Pillars evaluation
- ✅ Save with descriptive filename: `[feature]-[YYYY-MM-DD].md`
- ✅ Regenerate indexes after saving

**DON'T**:
- ❌ Generate specs without checking for existing related work
- ❌ Skip metadata (makes specs undiscoverable)
- ❌ Delete old specs (mark as `superseded` instead)
- ❌ Save specs outside `.design/specs/`
- ❌ Skip rationale section (preserve decision reasoning)

### Example Workflows

**New Feature Spec**:
```
1. User: "Design notification badge component"
2. Agent searches: grep -r "notification\|badge" .design/specs/
3. Agent finds: fab-implementation-2025-10-21.md (has badge)
4. Agent asks: "Found FAB spec with badge pattern. Reference it?"
5. User: "Yes"
6. Agent generates spec referencing FAB approach
7. Agent saves: .design/specs/notification-badge-2025-10-23.md
8. Agent updates: .design/specs/INDEX.md
9. Agent confirms: "Saved to .design/specs/notification-badge-2025-10-23.md"
```

**Update Existing Spec**:
```
1. User: "Update FAB spec with new animation timing"
2. Agent reads: .design/specs/fab-implementation-2025-10-21.md
3. Agent extracts: Original timing decisions and rationale
4. Agent generates: .design/specs/fab-implementation-2025-10-24.md
5. Agent updates old spec: status: superseded, superseded-by: fab-implementation-2025-10-24.md
6. Agent adds new metadata: supersedes: fab-implementation-2025-10-21.md
7. Agent includes: "Changes from Previous Spec" section
8. Agent updates index
```

### Integration with Protocols

Specs implement protocols:
- **COMPONENT-CREATION-PROTOCOL.md** → Defines "how to evaluate"
- **Specs** → Document "what was evaluated and decided"

Agents should:
1. Follow protocols when generating specs
2. Reference protocol sections in rationale
3. Include protocol checks in spec structure

### Maintenance

**Indexes are auto-generated** - never manually edit:
- `INDEX.md` (root)
- `.design/specs/INDEX.md`

**Regenerate anytime**:
```bash
.design/scripts/generate-master-index.sh
.design/scripts/generate-specs-index.sh
```

**Cleanup** (optional, quarterly):
- Move old superseded specs (>6 months) to `.design/archive/specs/`
- Keep recent specs in `.design/specs/` for easy discovery

## Key Files to Reference

- `studio-interface/app/globals.css` - All CSS variables MUST be defined here
- `studio-interface/state/store.ts` - Zustand global state management
- `studio-interface/components/icons/Icon.tsx` - Icon system
- `.design/COMPONENT-CREATION-PROTOCOL.md` - Component creation rules
- `.design/ANTI-PATTERNS.md` - Common mistakes to avoid
- `studio-interface/utils/designTokens.ts` - Utilities for reading CSS variables
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

## Establishing Project Aesthetic

**IMPORTANT:** The core Amplified Design system is aesthetic-agnostic. Each project defines its own aesthetic identity.

Before implementing any interface, establish the project's aesthetic:

### 1. Define Emotional Tone
- What should this feel like? (Playful vs serious? Warm vs precise?)
- What's the personality? (Energetic vs calm? Inviting vs professional?)
- What values does it embody? (Innovation vs tradition? Simplicity vs richness?)

### 2. Create Aesthetic Brief
```
Project: [name]
Context: [where/when this appears]
Emotional Goal: [feeling users should have]
Visual Approach: [style references, color philosophy]
Key Interaction: [signature moment]
References: [inspiration sources]
```

### 3. Document in `.design/AESTHETIC-GUIDE.md`
Create project-specific aesthetic guide containing:
- Emotional tone and personality
- Visual references and inspiration
- Color philosophy and palettes
- Interaction principles and timing
- Typography choices and hierarchy
- Spacing and proportion approach

### Example Project Aesthetics

**Studio-Interface Project** (reference implementation):
- **Homepage**: Swedish design studio aesthetic (playful, creative, inviting)
- **Workspace**: German car facility aesthetic (clean, focused, precise)
- See `.design/ARCHIVE-studio-creation/` for detailed example

**Other Aesthetic Approaches:**
- Japanese minimalism: Zen + wabi-sabi, beauty in imperfection
- American craft: Bold + tactile, handmade authenticity
- Brutalist digital: Raw + honest, function exposed
- Neo-Swiss: Systematic + rational, grid-based clarity

## CRITICAL: Aesthetic-First Implementation

**NEW WORKFLOW (2024-10-15):**
User feedback: "How do we get this kind of design thinking into our process earlier?"

**DO NOT implement in stages: "make it work" → "make it nice"**

Every implementation must start with aesthetic thinking:

### Step 1: Establish Emotional Tone (BEFORE coding)
Ask yourself:
- What should this *feel* like? (Playful, serious, inviting, confident?)
- What's the personality? (Creative vs. professional? Warm vs. precise?)
- What emotions should it evoke? (Curiosity, trust, delight, focus?)
- Reference: Project's `.design/AESTHETIC-GUIDE.md`

### Step 2: Design Brief (Quick alignment check)
```
Feature: [Name]
Emotional Goal: [What should this feel like?]
Visual Approach: [Colors from palette, interactions, timing]
Key Interaction: [The moment of delight]
Reference: [Similar thing done well]
```

Share this brief with user for alignment BEFORE implementing.

### Step 3: Implement with Polish Built-In

Every implementation must include refinement from the start:

### Required in First Pass:
- ✅ Functional implementation
- ✅ Refined micro-interactions (hover, focus, active states)
- ✅ Smooth transitions between states (choreographed, not abrupt)
- ✅ Premium feel (subtle depth, appropriate motion)
- ✅ 9.5/10 polish level

### Examples of First-Pass Refinement:

**Button** (not just functional):
- Hover: Subtle scale (1.02x) + brightness shift
- Active: Scale down (0.98x) + slight opacity
- Transition: 150ms cubic-bezier(0.4, 0, 0.2, 1)

**Page Transition** (not just component switch):
- Exit: Fade out + scale down (0.98x) over 300ms
- Breath: 50ms pause
- Enter: Staggered reveal (toolbar → canvas → chat)

**Empty State** (not just text):
- Interactive background (follows cursor)
- Auto-fire greeting animation
- Premium "front room" feel

**The Goal:** User should never have to say "this feels plain" or "add polish."
The polish should be intrinsic to the first implementation.

## Using Design Agents

Amplified Design provides specialized design agents in `.claude/agents/` to help apply the Nine Dimensions and Five Pillars philosophy systematically.

### The /designer Command

The `/designer` command orchestrates design work with automatic routing to appropriate specialists:

```bash
# Auto-route to appropriate agent
/designer [your design task]

# Direct routing
/designer system [task]      # → design-system-architect
/designer component [task]   # → component-designer
/designer animate [task]     # → animation-choreographer
```

### Design Agents Available

**design-system-architect** - System-level design decisions
- Design token architecture
- System-wide patterns and foundations
- Nine Dimensions evaluation
- Five Pillars validation
- Cross-cutting design concerns

**component-designer** - Individual component work
- Component design and refinement
- Props API design
- State handling (loading, error, empty, success)
- Variant creation
- Component documentation

**animation-choreographer** - Motion design
- Animation timing and easing
- Micro-interactions
- Page transitions
- Loading states
- Accessibility for motion

### Example Workflows

**Design System Work:**
```bash
/designer system Create motion timing tokens for micro-interactions
/designer system Define semantic color tokens for dark mode
```

**Component Design:**
```bash
/designer component Design a notification toast with all states
/designer component Design a button with primary, secondary, and ghost variants
```

**Motion Design:**
```bash
/designer animate Create a drawer slide-in animation
/designer animate Animate a success checkmark that draws in over 300ms
```

**Full Workflow:**
```bash
# 1. Design the component
/designer component Design a modal dialog

# 2. Implement from spec
Use the modular-builder agent to implement the modal from spec

# 3. Validate accessibility
Use the security-guardian agent to validate accessibility

# 4. Ensure quality
Use the test-coverage agent to ensure quality
```

### Amplifier Agents

General-purpose agents from the amplifier submodule are also available:

- **zen-architect** - Code architecture analysis and design
- **modular-builder** - Implementation from specifications
- **bug-hunter** - Systematic bug finding and fixing
- **test-coverage** - Test analysis and suggestions
- **security-guardian** - Security reviews and accessibility
- **performance-optimizer** - Performance analysis and optimization

Invoke via:
```
Use the zen-architect agent to analyze the code architecture
Use the modular-builder agent to implement this specification
```

See `.claude/README.md` for complete agent documentation.

## Working with Components

### Before Creating/Modifying a Component

1. **Articulate Purpose** (one clear sentence)
2. **Validate Need** (should this exist?)
3. **Check Tokens** (all CSS variables defined in globals.css?)
4. **Plan Refinement** (What micro-interactions? What transitions? What makes this feel premium?)
5. **Evaluate Against Nine Dimensions**:
   - Style: Visual language appropriate?
   - Motion: Timing follows protocol (<100ms, 100-300ms, 300-1000ms)?
   - Voice: Language matches personality?
   - Space: Follows 8px spacing system?
   - Color: Meets contrast requirements (4.5:1 text, 3:1 UI)?
   - Typography: Hierarchy clear and using system fonts?
   - Proportion: Balanced and appropriate scale?
   - Texture: Adds value without distraction?
   - Body: Touch targets meet minimums (44x44px or 48x48dp)?
6. **Check Five Pillars**:
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
