---
description: "Build, refine, and evaluate frontend interfaces with anti-slop design principles. Modes: build, teach, polish, audit, critique, harden, animate, typeset, colorize, arrange, bolder, quieter, distill, overdrive."
---

# /frontend-design — Unified Frontend Design Command

## Mode Detection

Parse `$ARGUMENTS`:
- Extract the first word and check against known modes: `teach`, `polish`, `audit`, `critique`, `harden`, `animate`, `typeset`, `colorize`, `arrange`, `bolder`, `quieter`, `distill`, `overdrive`
- If first word matches a mode: use that mode, pass remainder as target
- If no match: `build` mode, entire argument is target
- If empty: `build` mode, ask user what to create

---

## Context Protocol (ALL modes)

Before ANY mode executes:

1. **Load core principles**: Read `.claude/skills/frontend-design/PRINCIPLES.md` — contains design guidelines, anti-patterns, and the AI Slop Test
2. **Check loaded instructions**: Look for a `## Design Context` section in CLAUDE.md or project instructions — if found, use it as design context
3. **Check for .impeccable.md**: Read `.impeccable.md` at project root — if found, load it for brand/audience/aesthetic context
4. **Handle missing context**:
   - If no Design Context AND no `.impeccable.md` AND mode is `build` or `overdrive`: STOP and run `teach` mode first — these modes produce generic output without project context
   - If no context AND mode is a refinement mode (`polish`, `audit`, `critique`, `harden`, `animate`, `typeset`, `colorize`, `arrange`, `bolder`, `quieter`, `distill`): proceed without — the existing code IS the context

---

## Reference Documents

Modes that dispatch subagents inject these files as needed:

| Ref | Path | Used by |
|-----|------|---------|
| SKILL | `.claude/skills/frontend-design/PRINCIPLES.md` | All modes |
| ANTIPATTERNS | `ai_context/design/WEB-CODE-ANTIPATTERNS.md` | build, audit, harden |
| UX-CHECKLIST | `ai_context/design/UX-REVIEW-CHECKLIST.md` | audit, critique |
| TYPOGRAPHY | `.claude/skills/frontend-design/reference/typography.md` | typeset, build |
| COLOR | `.claude/skills/frontend-design/reference/color-and-contrast.md` | colorize, build |
| SPATIAL | `.claude/skills/frontend-design/reference/spatial-design.md` | arrange, build |
| MOTION | `.claude/skills/frontend-design/reference/motion-design.md` | animate, build |
| INTERACTION | `.claude/skills/frontend-design/reference/interaction-design.md` | harden, build |
| RESPONSIVE | `.claude/skills/frontend-design/reference/responsive-design.md` | build, polish |
| UX-WRITING | `.claude/skills/frontend-design/reference/ux-writing.md` | build, polish, critique |

---

## Modes

### build (default)

**Dispatch**: Sonnet subagent, `implement` role, 25-40 turns
**Inject**: SKILL + ANTIPATTERNS + .impeccable.md + all 7 reference docs (TYPOGRAPHY, COLOR, SPATIAL, MOTION, INTERACTION, RESPONSIVE, UX-WRITING)

Procedure:

1. **Stack detection**: Scan for `package.json`, `tailwind.config.*`, `*.razor`, `components/ui/` to determine framework and styling approach. Pass stack context to implementation.
2. **Design direction**: Commit to a BOLD aesthetic direction — purpose, tone, constraints, differentiation. Choose an extreme and execute with precision. Never converge on safe defaults.
3. **Propose approach**: Describe the visual direction and key design decisions. If ambiguous, ask user to pick between 2-3 directions.
4. **Implement**: Build production-grade, working code. Match implementation complexity to the aesthetic vision. Use distinctive fonts, intentional color, varied spacing, purposeful motion.
5. **AI Slop Test**: Review ALL DON'T guidelines from PRINCIPLES.md. If the interface looks like generic AI output (cyan-on-dark, gradient text, glassmorphism, identical card grids, Inter/Roboto), fix it before presenting.
6. **Verify**: Accessibility (WCAG AA contrast, 44px touch targets, keyboard nav, reduced motion), performance (transform/opacity only, no layout animation), responsiveness.

### teach

**Runs inline** (needs user dialogue, no subagent)

Procedure:

1. **Scan codebase**: README, package.json, CSS variables, existing components, brand assets, design tokens. Note what you learn and what remains unclear.
2. **Ask focused questions** (skip what's inferrable):
   - **Users & Purpose**: Who uses this? What job? What emotions should it evoke?
   - **Brand & Personality**: 3-word personality? Reference sites? Anti-references?
   - **Aesthetic Preferences**: Visual direction? Light/dark? Colors to use or avoid?
   - **Accessibility**: WCAG level? Known user needs?
3. **Write `.impeccable.md`** at project root with 4 sections:
   - `### Users` — who, context, job to be done
   - `### Brand Personality` — voice, tone, 3-word personality, emotional goals
   - `### Aesthetic Direction` — visual tone, references, anti-references, theme
   - `### Design Principles` — 3-5 principles derived from conversation
4. Ask if user also wants the Design Context appended to CLAUDE.md.

### polish

**Dispatch**: Sonnet subagent, `implement` role, 20-30 turns
**Inject**: SKILL + ANTIPATTERNS + RESPONSIVE + UX-WRITING + .impeccable.md

Systematic final pass across these dimensions:

1. **Visual Alignment** — pixel-perfect grid adherence, consistent spacing scale, optical alignment, responsive consistency
2. **Typography** — hierarchy consistency, 45-75 char line length, appropriate line-height, no FOUT/FOIT
3. **Color & Contrast** — WCAG ratios, consistent token usage, tinted neutrals (never pure gray), no gray-on-color
4. **8 Interaction States** — default, hover, focus, active, disabled, loading, error, success for every interactive element
5. **Micro-interactions** — smooth 150-300ms transitions, ease-out-quart/quint easing, 60fps, reduced motion support
6. **Content & Copy** — consistent terminology, capitalization, grammar, punctuation
7. **Icons & Images** — consistent style/sizing, alt text, no layout shift, retina support
8. **Forms** — labels, required indicators, error messages, tab order, validation timing
9. **Edge Cases** — loading states, empty states, error states, long content, no content, offline
10. **Responsive** — all breakpoints, 44px touch targets, 14px+ mobile text, no horizontal scroll
11. **Performance** — fast initial load, no CLS, smooth interactions, lazy loading
12. **Code Quality** — no console.logs, no commented code, no unused imports, no `any` types

**AI Slop Test**: Final check against all DON'T guidelines before marking done.

**Polish checklist** (all must pass):
- [ ] Visual alignment perfect at all breakpoints
- [ ] Spacing uses design tokens consistently
- [ ] Typography hierarchy consistent
- [ ] All interactive states implemented
- [ ] All transitions smooth (60fps)
- [ ] Copy consistent and polished
- [ ] Icons consistent and properly sized
- [ ] Forms properly labeled and validated
- [ ] Error/loading/empty states helpful
- [ ] Touch targets 44px+ minimum
- [ ] Contrast meets WCAG AA
- [ ] Keyboard navigation works
- [ ] Focus indicators visible
- [ ] No layout shift on load
- [ ] Respects reduced motion
- [ ] Code clean (no TODOs, console.logs, commented code)
- [ ] Passes AI Slop Test
- [ ] Verified on real devices (not just DevTools)

### audit

**Dispatch**: Haiku subagent, `scout` role, READ-ONLY, 12-20 turns
**Inject**: SKILL + ANTIPATTERNS + UX-CHECKLIST

Read-only diagnostic scan. Do NOT fix issues — document them.

Scan dimensions:
1. **Accessibility** — contrast, ARIA, keyboard nav, semantic HTML, alt text, form labels
2. **Performance** — layout thrashing, expensive animations, missing lazy loading, bundle size, re-renders
3. **Theming** — hardcoded colors, broken dark mode, inconsistent tokens
4. **Responsive** — fixed widths, small touch targets, horizontal scroll, missing breakpoints
5. **Anti-Patterns** — check ALL DON'T guidelines from PRINCIPLES.md for AI slop tells

**Report structure**:

```
### Anti-Patterns Verdict
Pass/fail: Does this look AI-generated? List specific tells. Be brutally honest.

### Executive Summary
Total issues by severity. Top 3-5 critical issues. Recommended next steps.

### Findings by Severity
For each: Location | Severity (Critical/High/Medium/Low) | Category | Description | Impact | Recommendation | Suggested /frontend-design mode to fix

### Systemic Issues
Recurring patterns across the codebase.

### Positive Findings
What's working well — practices to maintain.

### Fix Plan
Map issues to /frontend-design modes: polish, harden, colorize, typeset, arrange, etc.
```

### critique

**Dispatch**: Sonnet subagent, `review` role, READ-ONLY, 15-25 turns
**Inject**: SKILL + .impeccable.md + UX-CHECKLIST

Holistic design evaluation across 10 dimensions:

1. **AI Slop Detection** — does this look like every other AI interface from 2024-2025? Check ALL DON'T guidelines. This is the most important check.
2. **Visual Hierarchy** — does the eye flow correctly? Clear primary action visible in 2 seconds?
3. **Information Architecture** — intuitive structure? Logical grouping? Cognitive overload?
4. **Emotional Resonance** — what emotion does it evoke? Does it match brand personality?
5. **Discoverability** — are interactive elements obviously interactive? Useful hover/focus states?
6. **Composition & Balance** — balanced layout? Intentional whitespace? Visual rhythm?
7. **Typography** — clear type hierarchy? Comfortable reading? Font choices reinforce brand?
8. **Color with Purpose** — color communicates, not just decorates? Cohesive palette? Colorblind-safe?
9. **States & Edge Cases** — empty states guide action? Loading reduces perceived wait? Errors help?
10. **Microcopy & Voice** — clear, concise, human? Labels unambiguous? Errors actionable?

**Report structure**:

```
### Anti-Patterns Verdict
Pass/fail with specific tells.

### Overall Impression
Gut reaction — what works, what doesn't, single biggest opportunity.

### What's Working
2-3 specific strengths with reasons.

### Priority Issues (3-5)
Each: What | Why it matters | Concrete fix | Suggested /frontend-design mode

### Questions to Consider
Provocative questions to unlock better solutions.
```

### harden

**Dispatch**: Sonnet subagent, `implement` role, 20-35 turns
**Inject**: SKILL + ANTIPATTERNS + INTERACTION ref + .impeccable.md

Strengthen interfaces against real-world edge cases:

1. **Text Overflow** — truncation with ellipsis, multi-line clamp, `min-width: 0` on flex children, `overflow-wrap: break-word`, fluid `clamp()` sizing
2. **Internationalization** — 30-40% text expansion budget, logical CSS properties (`margin-inline-start`), RTL support, `Intl.DateTimeFormat`/`Intl.NumberFormat`, proper pluralization
3. **Error Handling** — network failures with retry, form validation inline near fields, HTTP status-specific handling (400/401/403/404/429/500), graceful degradation
4. **Edge Cases** — empty states with next action, loading states with context, large datasets (pagination/virtual scroll), concurrent operations (debounce/disable), permission states
5. **Input Validation** — required fields, format validation, length limits, pattern matching, server-side validation always
6. **Accessibility Resilience** — keyboard navigation, screen reader ARIA, `prefers-reduced-motion`, high contrast mode
7. **Performance Resilience** — progressive image loading, skeleton screens, cleanup event listeners/subscriptions, debounce/throttle handlers

Verify with extreme inputs: 100+ char names, emoji in all fields, RTL text, CJK characters, 1000+ list items, rapid repeated clicks, disabled network.

### animate

**Dispatch**: Sonnet subagent, `implement` role, 20-30 turns
**Inject**: SKILL + MOTION ref + .impeccable.md

Procedure:

1. **Assess opportunities** — identify missing feedback, jarring transitions, unclear relationships, joyless interactions
2. **Plan strategy** — define four layers:
   - **Hero moment**: ONE signature animation (page load? key interaction?)
   - **Feedback layer**: which interactions need acknowledgment
   - **Transition layer**: which state changes need smoothing
   - **Delight layer**: where to surprise users
3. **Implement** — entrance choreography (staggered 100-150ms delays), micro-interactions (hover scale 1.02-1.05, click 0.95-1.0), state transitions (200-300ms fade+slide), navigation (crossfade, tab indicators, scroll effects)
4. **Technical standards**: ease-out-quart/quint/expo only (NEVER bounce/elastic), transform+opacity only (NEVER animate width/height/top/left), `prefers-reduced-motion` always respected
5. **Verify 60fps** on target devices, appropriate timing (not too fast/slow), reduced motion alternative works

### typeset

**Dispatch**: Sonnet subagent, `implement` role, 15-25 turns
**Inject**: SKILL + TYPOGRAPHY ref + .impeccable.md

Procedure:

1. **Assess** — font choices (generic defaults?), hierarchy (clear at a glance?), scale (consistent ratio?), readability (45-75 char lines, 16px+ body), consistency (same elements styled same way)
2. **Plan** — font selection matching brand, modular type scale (1.25/1.333/1.5 ratio), weight strategy (3-4 weights max), spacing (line-height per context)
3. **Implement** — replace generic fonts with distinctive choices, establish 5-level hierarchy (caption/secondary/body/subheading/heading), fluid `clamp()` sizing, `tabular-nums` for data, semantic token names, proper `font-display: swap` loading
4. **Rules**: never use Inter/Roboto/Open Sans when personality matters, never set body below 16px, use `rem` not `px`, max 2-3 font families, load only weights you use
5. **Verify** — hierarchy identifiable instantly, body comfortable for long reading, consistent throughout, reflects brand, fonts load without layout shift, meets WCAG contrast

### colorize

**Dispatch**: Sonnet subagent, `implement` role, 15-25 turns
**Inject**: SKILL + COLOR ref + .impeccable.md

Procedure:

1. **Assess** — current color state (pure grayscale? one timid accent?), missed opportunities for semantic meaning/hierarchy/delight, existing brand colors
2. **Plan palette** — 2-4 colors beyond neutrals, dominant (60%), secondary (30%), accent (10%). Use OKLCH for perceptually uniform palettes.
3. **Apply systematically**:
   - **Semantic**: success/error/warning/info states, status badges, progress indicators
   - **Accent**: primary actions, links, key icons, section headers, hover states
   - **Surfaces**: tinted backgrounds (`oklch(97% 0.01 hue)` not pure gray), colored sections, subtle gradients (NOT purple-to-blue)
   - **Borders**: accent borders on cards/sections, colored focus rings, subtle dividers
4. **Balance** — 60/30/10 ratio, WCAG contrast compliance, don't rely on color alone, test for colorblindness, temperature consistency
5. **Rules**: never gray text on colored backgrounds (use darker shade of that color), never pure black/white for large areas, never purple-blue gradient defaults
6. **Verify** — color guides attention, adds meaning, feels engaging, meets WCAG, not overwhelming

### arrange

**Dispatch**: Sonnet subagent, `implement` role, 15-25 turns
**Inject**: SKILL + SPATIAL ref + .impeccable.md

Procedure:

1. **Assess** — spacing (consistent or arbitrary? all the same?), hierarchy (squint test — can you identify primary element with blurred vision?), grid (clear structure or random?), rhythm (alternating tight/generous or monotonous?), density (cramped or too sparse?)
2. **Plan** — consistent spacing scale (framework or custom), hierarchy strategy via space, layout tool (Flexbox for 1D, Grid for 2D), rhythm plan
3. **Implement**:
   - **Spacing system**: consistent scale, `gap` for siblings, `clamp()` for fluid spacing
   - **Visual rhythm**: tight grouping for related (8-12px), generous between sections (48-96px), varied within
   - **Layout tool**: Flexbox for most things, Grid only for 2D coordination, `repeat(auto-fit, minmax(280px, 1fr))` for responsive grids
   - **Break monotony**: don't default to card grids, vary card sizes, mix cards with non-card content, asymmetric compositions
4. **Squint test**: verify primary/secondary/groupings visible with blurred vision
5. **Rules**: never arbitrary spacing outside scale, never wrap everything in cards, never nest cards in cards, never center everything, never same spacing everywhere
6. **Verify** — satisfying rhythm of tight/generous, hierarchy obvious in 2 seconds, comfortable density, consistent scale, responsive

### bolder

**Dispatch**: Sonnet subagent, `implement` role, 20-30 turns
**Inject**: SKILL + .impeccable.md

**WARNING — AI SLOP TRAP**: When asked to make things "bolder," AI defaults to cyan gradients, glassmorphism, neon accents on dark backgrounds, gradient text. These are the OPPOSITE of bold — they're generic. Review ALL DON'T guidelines from PRINCIPLES.md before proceeding. Bold means distinctive, not "more effects."

Procedure:

1. **Assess weakness** — generic fonts, timid scale, low contrast, static/no motion, predictable layouts, flat hierarchy
2. **Plan amplification** — pick ONE focal point, choose a personality lane (maximalist chaos, elegant drama, playful energy, dark moody), set risk budget
3. **Amplify across 5 dimensions**:
   - **Typography**: distinctive fonts, extreme scale jumps (3-5x), weight contrast (900 vs 200), variable/display fonts
   - **Color**: increase saturation, unexpected combinations (not purple-blue), dominant color strategy, tinted neutrals, intentional gradients
   - **Space**: extreme scale jumps, break the grid, asymmetric layouts, generous whitespace (100-200px gaps), intentional overlap
   - **Effects**: dramatic shadows (not generic rounded-rect drop shadows), textures/grain/duotone (NOT glassmorphism), custom decorative elements
   - **Motion**: entrance choreography, scroll effects, micro-interactions, ease-out-quart/quint (never bounce/elastic)
4. **AI Slop Test**: If it looks like every other "bold" AI design, start over. Bold = distinctive, not "more AI effects."
5. **Verify** — still functional, coherent, memorable, performant, accessible

### quieter

**Dispatch**: Sonnet subagent, `implement` role, 15-25 turns
**Inject**: SKILL + .impeccable.md

Procedure:

1. **Identify intensity sources** — oversaturated colors, extreme contrast, too many heavy elements, excessive animation, visual complexity, everything loud with no hierarchy
2. **Plan refinement** — desaturate or shift to sophisticated tones, pick which few elements stay bold, identify what to remove entirely, signal quality through restraint
3. **Reduce systematically**:
   - **Color**: 70-85% saturation, muted tones, fewer colors, neutrals do more work, tinted grays
   - **Visual weight**: reduce font weights (900→600), lighter borders/lower opacity, more whitespace
   - **Simplification**: remove decorative gradients/shadows/patterns, simplify shapes, flatten layering
   - **Motion**: shorter distances (10-20px), remove decorative animations, keep functional motion, ease-out-quart
   - **Composition**: smaller scale jumps, return rogue elements to grid, consistent rhythm
4. **Rules**: don't make everything same size (hierarchy matters), don't remove all color, preserve personality, maintain clear affordances
5. **Verify** — still functional, still distinctive, better for extended reading, feels sophisticated not boring

### distill

**Dispatch**: Sonnet subagent, `implement` role, 15-25 turns
**Inject**: SKILL + .impeccable.md

Procedure:

1. **Identify complexity** — too many elements, excessive variation, information overload, visual noise, confusing hierarchy, feature creep
2. **Find essence** — what's the ONE primary user goal? What's the 20% delivering 80% of value?
3. **Simplify across 6 dimensions**:
   - **IA**: remove secondary actions, progressive disclosure, combine related actions, ONE primary action, remove redundancy
   - **Visual**: 1-2 colors + neutrals, one font family / 3-4 sizes / 2-3 weights, remove decorations that don't serve hierarchy, remove unnecessary cards
   - **Layout**: linear flow where possible, remove sidebars, generous whitespace, consistent alignment
   - **Interaction**: fewer choices, smart defaults, inline over modal, reduce steps, ONE obvious CTA
   - **Content**: cut copy in half twice, active voice, plain language, scannable structure, no repeated explanations
   - **Code**: remove dead CSS/components, flatten component trees, consolidate styles, reduce variants
4. **Verify completeness** — users can still accomplish goals, all necessary features accessible, hierarchy clear
5. **Document what was removed** and why — note if alternative access points are needed

### overdrive

**Runs inline** (Opus) — technically ambitious, needs deep reasoning

**MUST propose 2-3 directions and ASK USER before building.** This mode has the highest potential to misfire.

Procedure:

1. **Assess what "extraordinary" means here**:
   - Visual/marketing surfaces: sensory wow (shaders, scroll-driven reveals, cinematic transitions)
   - Functional UI: feel wow (View Transitions morphing, virtual scroll 60fps, streaming validation)
   - Performance-critical: invisible wow (50k items filtered without flicker, never blocks main thread)
   - Data-heavy: fluidity wow (GPU-accelerated charts, animated data transitions, force-directed graphs)
2. **Propose 2-3 directions** with trade-offs (browser support, performance cost, complexity). STOP and ask user to pick before writing any code.
3. **Toolkit** (use what fits):
   - View Transitions API — shared element morphing between states
   - `@starting-style` — CSS-only animate from `display: none`
   - Spring physics — natural motion with mass/tension/damping
   - Scroll-driven animations — `animation-timeline: scroll()`, CSS-only
   - WebGL/WebGPU — shader effects, particle systems, post-processing
   - Canvas/OffscreenCanvas — custom rendering, off-main-thread
   - `@property` — animate gradients and complex CSS values
   - Web Animations API — composable, cancellable JS animations
   - Web Workers — computation off main thread
   - Virtual scrolling — render only visible rows for massive lists
4. **Progressive enhancement is non-negotiable** — `@supports` for CSS features, capability detection for APIs, beautiful static fallback always
5. **Performance rules**: target 60fps, respect `prefers-reduced-motion`, lazy-init heavy resources, pause off-screen rendering, test on mid-range devices
6. **Iterate visually** — use browser automation to preview, verify, and refine. The gap between "works" and "extraordinary" is closed through visual iteration.
7. **Verify**: wow test (do people react?), removal test (would its absence be felt?), device test (smooth on phone?), accessibility test (beautiful with reduced motion?), context test (appropriate for this brand?)
