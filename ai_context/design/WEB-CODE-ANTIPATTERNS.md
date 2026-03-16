# Web Code Anti-Patterns & Micro-Rules

Code-level companion to UX-REVIEW-CHECKLIST.md. Use during code review and implementation to catch common web development mistakes. Output format: `file:line — issue`.

Adapted from [Vercel Web Interface Guidelines](https://github.com/vercel-labs/web-interface-guidelines).

---

## Anti-Patterns (flag these in code review)

- `user-scalable=no` or `maximum-scale=1` — disables zoom, breaks accessibility
- `onPaste` with `preventDefault` — never block paste on inputs
- `transition: all` — list properties explicitly (`transition: opacity 150ms, transform 150ms`)
- `outline: none` / `outline-none` without `:focus-visible` replacement — removes keyboard focus indicator
- `<div onClick>` or `<span onClick>` — use `<button>` for actions, `<a>` for navigation
- Images without `width`/`height` — causes CLS (layout shift)
- Large arrays `.map()` without virtualization (50+ items)
- Form inputs without `<label>` or `aria-label`
- Icon buttons without `aria-label`
- Hardcoded date/number formats — use `Intl.DateTimeFormat` / `Intl.NumberFormat`
- `autoFocus` without justification — avoid on mobile entirely
- Inline styles for layout — use flex/grid, not JS measurement

---

## Micro-Typography

- `…` not `...` (proper ellipsis character)
- Curly quotes `"` `"` not straight `"` in UI copy
- Non-breaking spaces: `10&nbsp;MB`, `⌘&nbsp;K`, brand names
- Loading states end with `…`: "Loading…", "Saving…", "Connecting…"
- `font-variant-numeric: tabular-nums` on number columns, prices, timers
- `text-wrap: balance` or `text-pretty` on headings (prevents orphan words)

---

## Content Handling

- Text containers must handle long content: `truncate`, `line-clamp-*`, or `break-words`
- Flex children need `min-w-0` to allow text truncation (without it, flex items won't shrink below content width)
- Handle empty states — never render broken UI for empty strings/arrays
- User-generated content: design for short, average, AND very long inputs
- Placeholders end with `…` and show example pattern (e.g., "Search products…")

---

## Forms (code-level rules)

- Inputs need `autocomplete` attribute and meaningful `name`
- Use correct `type`: `email`, `tel`, `url`, `number` + `inputmode` for mobile keyboard
- Labels must be clickable (`htmlFor` or wrapping the control)
- Disable `spellCheck` on emails, codes, usernames
- Checkboxes/radios: label + control share single hit target (no dead zones between them)
- Submit button stays enabled until request starts; show spinner during request
- Errors inline next to fields; auto-focus first error on submit
- `autocomplete="off"` on non-auth fields (avoids password manager false triggers)
- Warn before navigation with unsaved changes (`beforeunload` or router guard)

---

## Focus & Keyboard

- Interactive elements need visible focus: `focus-visible:ring-*` or equivalent
- Never `outline-none` without a `:focus-visible` replacement
- Use `:focus-visible` over `:focus` (avoids focus ring on mouse click)
- Group focus with `:focus-within` for compound controls (e.g., search bar with button)
- Keyboard handlers: interactive custom elements need `onKeyDown`/`onKeyUp`

---

## Navigation & URL State

- URL must reflect state — filters, tabs, pagination, expanded panels in query params
- If it uses `useState`, consider URL sync (nuqs, `useSearchParams`, or equivalent)
- Links use `<a>` / `<Link>` — must support Cmd/Ctrl+click and middle-click
- Deep-link all stateful UI — users should be able to share/bookmark any view state
- Destructive actions need confirmation modal or undo window — never immediate delete

---

## Touch & Mobile

- `touch-action: manipulation` on interactive areas (prevents 300ms double-tap delay)
- `overscroll-behavior: contain` on modals/drawers/sheets (prevents background scroll)
- During drag: disable text selection, set `inert` on dragged elements
- `autoFocus` on desktop only, single primary input — skip on mobile

---

## Safe Areas & Layout

- Full-bleed layouts need `env(safe-area-inset-*)` for notches/Dynamic Island
- Avoid unwanted scrollbars: `overflow-x-hidden` on containers, fix content overflow
- Use flex/grid for layout, not JS measurement (`getBoundingClientRect` in render)

---

## Dark Mode (code-level)

- Set `color-scheme: dark` on `<html>` for dark themes (fixes native scrollbar, inputs, selects)
- `<meta name="theme-color">` should match page background color
- Native `<select>`: set explicit `background-color` and `color` (Windows dark mode breaks defaults)

---

## i18n & Locale

- Dates/times: `Intl.DateTimeFormat` — never hardcode formats like `MM/DD/YYYY`
- Numbers/currency: `Intl.NumberFormat` — never hardcode `$` or comma separators
- Detect language via `Accept-Language` / `navigator.languages`, not IP geolocation

---

## Hydration Safety (React/Next.js)

- Inputs with `value` need `onChange` (or use `defaultValue` for uncontrolled)
- Date/time rendering: guard against hydration mismatch (server vs client timezone)
- `suppressHydrationWarning` only where truly needed — not as a blanket fix

---

## Copy & Voice (code-level)

- Active voice: "Install the CLI" not "The CLI will be installed"
- Title Case for headings/buttons (Chicago style)
- Numerals for counts: "8 deployments" not "eight deployments"
- Specific button labels: "Save API Key" not "Continue" or "Submit"
- Error messages include fix/next step, not just the problem
- `&` over "and" where space-constrained (button labels, tabs)
