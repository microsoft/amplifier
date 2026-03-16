# UX Review Checklist

Prioritized checklist for UI/UX review. Use during `component-designer`, `frontend-design`, `/browser-audit`, and any frontend implementation review. Work priority 1→10.

Adapted from [ui-ux-pro-max](https://github.com/nextlevelbuilder/ui-ux-pro-max-skill) — condensed to actionable checks.

---

## Priority 1: Accessibility (CRITICAL)

- [ ] Color contrast ≥ 4.5:1 for normal text, ≥ 3:1 for large text
- [ ] Visible focus rings on all interactive elements (2-4px)
- [ ] Alt text on all meaningful images
- [ ] `aria-label` on icon-only buttons
- [ ] Tab order matches visual order; full keyboard navigation works
- [ ] `<label>` with `for` on all form inputs
- [ ] Skip-to-main-content link present
- [ ] Heading hierarchy sequential (h1→h2→h3, no level skip)
- [ ] Information not conveyed by color alone (add icon/text)
- [ ] `prefers-reduced-motion` respected — animations reduced/disabled
- [ ] Screen reader labels meaningful and logically ordered

## Priority 2: Touch & Interaction (CRITICAL)

- [ ] Touch targets ≥ 44×44px (iOS) / 48×48dp (Android)
- [ ] ≥ 8px gap between touch targets
- [ ] Primary interactions use click/tap, not hover-only
- [ ] Buttons disabled + spinner during async operations
- [ ] Error messages appear near the problem field
- [ ] `cursor: pointer` on all clickable elements (web)
- [ ] No horizontal swipe conflicts with main scroll
- [ ] Visual press feedback (ripple, highlight, scale)
- [ ] Safe area awareness (notch, gesture bar, screen edges)

## Priority 3: Performance (HIGH)

- [ ] Images use WebP/AVIF with `srcset`/`sizes`
- [ ] Images have `width`/`height` or `aspect-ratio` (prevents CLS)
- [ ] `font-display: swap` on web fonts
- [ ] Lazy load below-fold content
- [ ] Code split by route/feature
- [ ] No layout thrashing (batch DOM reads then writes)
- [ ] Skeleton/shimmer for loads > 300ms
- [ ] Virtualize lists with 50+ items
- [ ] Input latency < 100ms for taps/scrolls
- [ ] `debounce`/`throttle` on high-frequency events

## Priority 4: Style Selection (HIGH)

- [ ] Style matches product type consistently across all pages
- [ ] SVG icons (Heroicons, Lucide) — never emoji as icons
- [ ] Shadows, blur, radius consistent with chosen style
- [ ] Hover/pressed/disabled states visually distinct
- [ ] Consistent elevation/shadow scale (cards, sheets, modals)
- [ ] Light/dark variants designed together
- [ ] One icon set/visual language throughout
- [ ] One primary CTA per screen; secondary actions visually subordinate

## Priority 5: Layout & Responsive (HIGH)

- [ ] `<meta name="viewport" content="width=device-width, initial-scale=1">` — never disable zoom
- [ ] Mobile-first design, scale up to tablet/desktop
- [ ] Systematic breakpoints (375 / 768 / 1024 / 1440)
- [ ] Body text ≥ 16px on mobile (prevents iOS auto-zoom)
- [ ] No horizontal scroll on mobile
- [ ] 4px/8dp spacing system
- [ ] Consistent `max-width` on desktop containers
- [ ] Fixed navbar/bottom bar reserves safe padding for content
- [ ] `min-h-dvh` instead of `100vh` on mobile
- [ ] Visual hierarchy via size/spacing/contrast, not color alone

## Priority 6: Typography & Color (MEDIUM)

- [ ] Line-height 1.5-1.75 for body text
- [ ] Line length 60-75 characters (desktop), 35-60 (mobile)
- [ ] Heading/body font pairing has intentional personality contrast
- [ ] Consistent type scale (e.g., 12/14/16/18/24/32)
- [ ] Semantic color tokens (primary, error, surface) not raw hex
- [ ] Dark mode uses desaturated/lighter tonal variants (not inverted)
- [ ] Foreground/background pairs meet WCAG AA (4.5:1)
- [ ] Tabular/monospace figures for data columns, prices, timers
- [ ] Whitespace used intentionally to group/separate

## Priority 7: Animation (MEDIUM)

- [ ] Micro-interactions 150-300ms; complex transitions ≤ 400ms
- [ ] Only animate `transform` and `opacity` (never width/height/top/left)
- [ ] Max 1-2 animated elements per view
- [ ] `ease-out` for entering, `ease-in` for exiting
- [ ] Every animation conveys cause-effect, not decoration
- [ ] Exit animations shorter than enter (~60-70% duration)
- [ ] Stagger list items by 30-50ms per item
- [ ] Animations interruptible — user tap cancels immediately
- [ ] Never block user input during animation
- [ ] Modals animate from trigger source (scale+fade or slide)

## Priority 8: Forms & Feedback (MEDIUM)

- [ ] Visible label per input (not placeholder-only)
- [ ] Errors shown below the related field
- [ ] Loading → success/error state on submit
- [ ] Required fields marked (asterisk)
- [ ] Helpful empty states with action guidance
- [ ] Auto-dismiss toasts in 3-5s
- [ ] Confirm before destructive actions
- [ ] Validate on blur, not on keystroke
- [ ] Semantic input types (email, tel, number) for correct mobile keyboard
- [ ] Show/hide toggle for password fields
- [ ] Error messages state cause + how to fix (not just "Invalid input")
- [ ] After submit error, auto-focus first invalid field
- [ ] Destructive actions use danger color, visually separated from primary

## Priority 9: Navigation (HIGH)

- [ ] Bottom nav ≤ 5 items with labels + icons
- [ ] Back navigation predictable, preserves scroll/state
- [ ] All key screens reachable via deep link / URL
- [ ] Current location visually highlighted in navigation
- [ ] Modals/sheets have clear close/dismiss affordance
- [ ] Search easily reachable (top bar or tab)
- [ ] Web: breadcrumbs for 3+ level deep hierarchies
- [ ] Navigation placement consistent across all pages
- [ ] Don't mix Tab + Sidebar + Bottom Nav at same level
- [ ] Dangerous actions (delete, logout) spatially separated from normal nav

## Priority 10: Charts & Data (LOW)

- [ ] Chart type matches data type (trend→line, comparison→bar, proportion→donut)
- [ ] Accessible colors — not red/green only; use patterns/textures too
- [ ] Table alternative provided for screen readers
- [ ] Legends visible near chart
- [ ] Tooltips on hover (web) / tap (mobile) with exact values
- [ ] Axes labeled with units and readable scale
- [ ] Charts reflow on small screens
- [ ] Empty state when no data ("No data yet" + guidance)
- [ ] Avoid pie charts for > 5 categories
- [ ] Data lines/bars vs background ≥ 3:1 contrast
