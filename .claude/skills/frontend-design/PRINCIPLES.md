# Frontend Design — Core Principles

> Reference document loaded by `/frontend-design` command. Not a standalone skill.

## Context Gathering Protocol

Before any design work:

1. **Check loaded instructions** — Look for a `## Design Context` section in CLAUDE.md or project instructions. If found, use it.
2. **Check .impeccable.md** — Look for `.impeccable.md` at the project root. If found, read it.
3. **Neither found** — Run `/frontend-design teach` before proceeding. Do not guess at design direction.

Required context: target audience, use cases, brand personality/tone. Code tells you what was built — only the creator can say who it's for and what it should feel like.

## The AI Slop Test

**Critical quality gate**: If you showed this interface to someone and said "AI made this," would they believe you immediately? If yes, that's the problem.

A distinctive interface makes someone ask "how was this made?" — not "which AI made this?"

The DON'T lists below are the fingerprints of AI-generated work from 2024–2025. Avoid them deliberately.

## Design Direction Framework

Before designing anything, define:
- **Purpose**: What does this interface help the user accomplish?
- **Tone**: Pick an extreme and commit — brutally minimal, maximalist, editorial, retro-futuristic, industrial, luxury, etc.
- **Constraints**: Technical, brand, and accessibility limits.
- **Differentiation**: What makes this unforgettable? What's the one thing someone will remember?

Bold maximalism and refined minimalism both work. The key is intentionality, not intensity.

## Aesthetic Guidelines

### Typography

DO: Use a modular type scale with fluid sizing (`clamp()`); vary weights and sizes for clear hierarchy
DON'T: Use Inter, Roboto, Arial, Open Sans, or system defaults — they signal zero typographic intention
DON'T: Use monospace as lazy shorthand for "technical" vibes
DON'T: Put large rounded-corner icons above every heading — templated, not designed
→ *Consult reference/typography.md for scales, fluid sizing, OpenType features, and font pairings*

### Color & Contrast

DO: Use modern CSS color functions (`oklch`, `color-mix`, `light-dark`) for perceptually uniform palettes
DO: Tint neutrals toward your brand hue — even subtle hints create subconscious cohesion
DON'T: Use the AI color palette: cyan-on-dark, purple-to-blue gradients, neon accents on dark
DON'T: Use gradient text on headings or metrics — decorative, not meaningful
DON'T: Default to dark mode with glowing accents — looks cool without actual design decisions
DON'T: Use pure black (#000) or pure white (#fff) — always tint
→ *Consult reference/color-and-contrast.md for OKLCH, tinted neutrals, token strategy*

### Spatial Design

DO: Create visual rhythm through varied spacing — tight groupings, generous separations
DO: Use `clamp()` for fluid spacing that breathes on larger screens
DO: Use asymmetry intentionally; break the grid for emphasis
DON'T: Wrap everything in cards — not everything needs a container
DON'T: Nest cards inside cards — flatten the hierarchy
DON'T: Use identical card grids: icon + heading + text, repeated endlessly
DON'T: Use the hero metric template: big number, small label, supporting stats, gradient accent
DON'T: Center everything — left-aligned text with asymmetric layouts feels more designed
→ *Consult reference/spatial-design.md for grids, rhythm, and container queries*

### Motion

DO: Use motion to convey state changes — entrances, exits, feedback
DO: Use exponential easing (`ease-out-quart`, `ease-out-expo`) for natural deceleration
DO: Animate height via `grid-template-rows` transitions, not `height` directly
DON'T: Animate layout properties (width, height, padding, margin) — use `transform` and `opacity` only
DON'T: Use bounce or elastic easing — dated; real objects decelerate smoothly
→ *Consult reference/motion-design.md for timing thresholds, easing curves, and reduced motion*

### Interaction

DO: Use progressive disclosure — basic options first, advanced behind expandable sections
DO: Design empty states that teach the interface, not just say "nothing here"
DO: Use optimistic UI — update immediately, sync later
DON'T: Make every button primary — use ghost, text links, and secondary styles; hierarchy matters
DON'T: Use modals unless there is truly no better alternative
DON'T: Use glassmorphism decoratively — blur and glow borders used without purpose
→ *Consult reference/interaction-design.md for forms, focus, and loading patterns*

### Responsive

DO: Use container queries (`@container`) for component-level responsiveness
DO: Adapt the interface for different contexts — don't just shrink it
DON'T: Hide critical functionality on mobile — adapt, don't amputate
→ *Consult reference/responsive-design.md for mobile-first and fluid design patterns*

### UX Writing

DO: Make every word earn its place; use specific language over generic
DON'T: Repeat information users can already see — redundant headers, intros that restate the heading
DON'T: Use generic CTA labels ("Submit", "Click here") when specific ones are available
→ *Consult reference/ux-writing.md for labels, errors, and empty states*

## Quality Dimensions

| Dimension | Check |
|-----------|-------|
| Style | Does it have a distinctive visual identity, not generic AI output? |
| Composition | Is the visual hierarchy clear — primary, secondary, tertiary? |
| Space | Is whitespace intentional? Breathing room where needed, density where appropriate? |
| Motion | Are animations purposeful? Do they respect `prefers-reduced-motion`? |
| Voice | Is the copy clear, specific, and consistent in tone across all touchpoints? |
| Density | Is information density appropriate for the audience and context? |
| Contrast | Does it meet WCAG AA — 4.5:1 for text, 3:1 for UI components? |
| Depth | Is elevation and layering used intentionally, not decoratively? |
| Rhythm | Is there consistent vertical rhythm and a coherent spacing scale? |

## Implementation Principles

- Semantic HTML first — ARIA as supplement, not substitute
- CSS custom properties for all design tokens
- Progressive enhancement — core content works without JS
- Mobile-first responsive — start narrow, add complexity upward
- Performance budget — question every dependency and large asset
- Accessibility is non-negotiable, not a post-launch checklist item
- No design should converge on common AI choices — vary fonts, themes, aesthetics deliberately
