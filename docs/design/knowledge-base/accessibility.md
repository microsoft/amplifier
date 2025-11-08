# Accessibility (a11y) for Design Systems

## Core Philosophy
**Accessibility is not optional. It's a baseline requirement, not a feature.**

One in four adults in the US has a disability. Accessible design benefits everyone, not just people with disabilities.

## WCAG 2.1 Guidelines Overview

### Level A (Minimum)
Must-haves for basic accessibility. Failure = significant barriers.

### Level AA (Standard)
Industry standard for most websites/apps. Required by many laws (ADA, Section 508).

### Level AAA (Enhanced)
Gold standard. Often impractical for entire sites, but achievable for critical flows.

## The Four Principles (POUR)

### 1. Perceivable
Information must be presentable to users in ways they can perceive.

**1.1 Text Alternatives**
- All images have alt text (or `alt=""` if decorative)
- Icons have accessible labels
- Complex graphics have long descriptions

**1.2 Time-Based Media**
- Videos have captions
- Audio has transcripts
- Purely visual/audio content has alternatives

**1.3 Adaptable**
- Semantic HTML (headings, lists, tables)
- Logical reading order
- Instructions don't rely on shape/size/location
- Content works in portrait and landscape

**1.4 Distinguishable**
- Text contrast: 4.5:1 (AA), 7:1 (AAA)
- Large text contrast: 3:1 (18pt+ or 14pt+ bold)
- Non-text contrast: 3:1 (icons, UI components)
- No color-only indicators (add icons/patterns)
- Text resizable to 200% without breaking
- Images of text avoided (use real text)
- Audio background 20dB quieter than foreground

### 2. Operable
Users must be able to operate the interface.

**2.1 Keyboard Accessible**
- All functionality available via keyboard
- No keyboard traps (can navigate away)
- Focus visible (2px outline, 3:1 contrast)
- Shortcut keys don't conflict with assistive tech

**2.2 Enough Time**
- Time limits adjustable/extendable
- Auto-updating content can be paused
- Re-authentication doesn't lose data
- Timeouts warned at least 20 seconds before

**2.3 Seizures and Physical Reactions**
- No flashing content (> 3 flashes per second)
- Motion parallax can be disabled

**2.4 Navigable**
- Skip links to main content
- Descriptive page titles
- Logical focus order
- Link purpose clear from text (or context)
- Multiple navigation methods (menu, search, sitemap)
- Headings and labels descriptive
- Focus indicator visible

**2.5 Input Modalities**
- Touch targets: 44x44px minimum (iOS), 48x48px (Android)
- Gestures have keyboard/click alternatives
- Labels match accessible names
- Motion actuation (shake, tilt) has alternatives

### 3. Understandable
Information and operation must be understandable.

**3.1 Readable**
- Page language declared (`<html lang="en">`)
- Language changes marked (`<span lang="es">`)
- Uncommon words/jargon explained
- Abbreviations/acronyms defined on first use
- Reading level: lower secondary education (Grade 8-9)

**3.2 Predictable**
- Focus doesn't trigger unexpected context changes
- Input doesn't trigger unexpected changes
- Navigation consistent across pages
- Repeated components appear in same order
- Icons/buttons have consistent functionality

**3.3 Input Assistance**
- Clear error identification
- Labels/instructions provided for inputs
- Error suggestions provided
- Form validation prevents errors
- Confirmation for legal/financial/data deletion actions

### 4. Robust
Content must work with current and future tools.

**4.1 Compatible**
- Valid HTML (no unclosed tags, duplicate IDs)
- ARIA used correctly
- Status messages announced to screen readers

## Color & Contrast

### Text Contrast
| Text Size | AA | AAA |
|-----------|-----|-----|
| Normal (<18pt) | 4.5:1 | 7:1 |
| Large (≥18pt or ≥14pt bold) | 3:1 | 4.5:1 |

### Non-Text Contrast (3:1)
- Icons and meaningful graphics
- Focus indicators
- UI component boundaries (buttons, inputs)
- States (hover, active, disabled)

### Testing Tools
- Chrome DevTools Lighthouse
- WebAIM Contrast Checker
- Stark (Figma/browser plugin)
- Colour Contrast Analyser (desktop app)

### Color-Blind Friendly
8% of men, 0.5% of women have color vision deficiency.

**Never rely on color alone:**
```html
<!-- BAD -->
<span style="color: red">Error</span>

<!-- GOOD -->
<span style="color: red">
  <svg aria-hidden="true"><use href="#error-icon"/></svg>
  Error
</span>
```

**Test with simulators:**
- Protanopia (red-blind)
- Deuteranopia (green-blind)
- Tritanopia (blue-blind)

## Keyboard Navigation

### Focus Management

**Visible Focus Indicator**
```css
:focus-visible {
  outline: 2px solid var(--focus-color);
  outline-offset: 2px;
}
```

**Focus Order**
- Matches visual order (left-to-right, top-to-bottom)
- Logical grouping (form fields together)
- Skip repetitive navigation (skip links)

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| Tab | Move forward |
| Shift + Tab | Move backward |
| Enter | Activate links/buttons |
| Space | Activate buttons, check checkboxes |
| Arrow Keys | Navigate within components (dropdowns, tabs) |
| Escape | Close modals/menus |
| Home/End | Jump to start/end of list |

### Interactive Component Patterns

**Button**
- Focusable: Yes
- Role: button
- Keys: Enter, Space

**Link**
- Focusable: Yes
- Role: link
- Keys: Enter

**Checkbox**
- Focusable: Yes
- Role: checkbox
- Keys: Space (toggle)

**Radio Group**
- Focusable: Yes (one at a time)
- Role: radiogroup, radio
- Keys: Arrow keys (navigate), Space (select)

**Dropdown/Select**
- Focusable: Yes
- Role: combobox, listbox
- Keys: Arrow keys (navigate), Enter (select), Escape (close)

**Modal/Dialog**
- Focus trapped inside modal
- Role: dialog
- Keys: Escape (close)
- aria-modal="true"

## Screen Reader Support

### Semantic HTML
```html
<!-- Use semantic elements -->
<header>, <nav>, <main>, <aside>, <footer>
<h1> to <h6>
<ul>, <ol>, <li>
<table>, <thead>, <tbody>, <tr>, <th>, <td>
<button>, <a>, <input>, <label>
```

### ARIA (when semantic HTML isn't enough)

**Landmark Roles**
```html
<div role="banner"><!-- site header --></div>
<div role="navigation"><!-- nav menu --></div>
<div role="main"><!-- main content --></div>
<div role="complementary"><!-- sidebar --></div>
<div role="contentinfo"><!-- footer --></div>
<div role="search"><!-- search form --></div>
```

**Common ARIA Attributes**

**aria-label**: Provides accessible name
```html
<button aria-label="Close dialog">
  <svg>×</svg>
</button>
```

**aria-labelledby**: References another element for label
```html
<h2 id="dialog-title">Delete Account</h2>
<div role="dialog" aria-labelledby="dialog-title">
```

**aria-describedby**: References another element for description
```html
<input id="email" aria-describedby="email-hint">
<span id="email-hint">We'll never share your email.</span>
```

**aria-hidden**: Hides from screen readers
```html
<svg aria-hidden="true"><!-- decorative icon --></svg>
```

**aria-live**: Announces dynamic content
```html
<!-- Polite: waits for screen reader to finish -->
<div aria-live="polite" aria-atomic="true">
  Changes saved!
</div>

<!-- Assertive: interrupts immediately -->
<div aria-live="assertive" role="alert">
  Error: Payment failed!
</div>
```

**aria-expanded**: For collapsible content
```html
<button aria-expanded="false" aria-controls="menu">
  Menu
</button>
<div id="menu" hidden>...</div>
```

**aria-current**: Indicates current item
```html
<a href="/about" aria-current="page">About</a>
```

### Screen Reader Testing
- **macOS**: VoiceOver (Cmd + F5)
- **Windows**: NVDA (free), JAWS (paid)
- **iOS**: VoiceOver (Settings > Accessibility)
- **Android**: TalkBack (Settings > Accessibility)

### Common Mistakes
1. **Empty links/buttons**: No text or aria-label
2. **Missing alt text**: Images without alternatives
3. **Poor heading structure**: Skipping levels (h1 → h3)
4. **Form labels**: Inputs without associated labels
5. **Focus traps**: Can't navigate away with keyboard
6. **Incorrect ARIA**: Misusing roles/properties

## Forms

### Labels
```html
<!-- Explicit label (preferred) -->
<label for="email">Email</label>
<input id="email" type="email">

<!-- Implicit label -->
<label>
  Email
  <input type="email">
</label>

<!-- aria-label (when visual label not possible) -->
<input type="search" aria-label="Search products">
```

### Error Handling
```html
<!-- Identify error -->
<label for="email">
  Email
  <span id="email-error" class="error">Invalid email format</span>
</label>
<input
  id="email"
  type="email"
  aria-invalid="true"
  aria-describedby="email-error"
>

<!-- Success message -->
<div role="status" aria-live="polite">
  Form submitted successfully!
</div>
```

### Required Fields
```html
<label for="name">
  Name
  <abbr title="required" aria-label="required">*</abbr>
</label>
<input id="name" required aria-required="true">
```

## Touch & Mobile

### Touch Targets
- **Minimum**: 44x44px (iOS), 48x48px (Android)
- **Recommended**: 48x48px with 8px spacing
- **Ideal**: 56x56px for primary actions

### Gestures
- Provide alternatives for complex gestures
- Single-finger alternatives for multi-finger gestures
- No motion-only controls (shake to undo)

### Zoom
- Allow pinch-to-zoom
- Text resizes without horizontal scrolling
- No `user-scalable=no`

## Animation & Motion

### Reduced Motion
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
  }
}
```

### Safe Animations
- No flashing content (≤3 flashes/second)
- Provide pause/stop controls for auto-playing content
- Parallax scrolling can trigger vestibular issues

## Testing Checklist

### Automated Testing (catches ~30%)
- [ ] Lighthouse accessibility audit
- [ ] axe DevTools
- [ ] WAVE browser extension
- [ ] Pa11y (command line)

### Manual Testing (catches the other 70%)
- [ ] Keyboard navigation (Tab, Shift+Tab, Enter, Space, Arrows, Escape)
- [ ] Screen reader (VoiceOver, NVDA, JAWS)
- [ ] Zoom to 200%
- [ ] Color contrast (text, icons, UI components)
- [ ] Color-blind simulation (Protanopia, Deuteranopia, Tritanopia)
- [ ] Reduced motion (prefers-reduced-motion)
- [ ] Touch targets (mobile/tablet)
- [ ] Focus indicators visible
- [ ] Forms with validation errors
- [ ] Modal focus traps

### User Testing (the gold standard)
- People who use assistive technology daily
- Diverse disabilities (vision, motor, cognitive, hearing)
- Real devices and assistive tech

## Common Components

### Button
```html
<button type="button">
  <svg aria-hidden="true"><!-- icon --></svg>
  Click Me
</button>
```

### Icon Button
```html
<button aria-label="Close" type="button">
  <svg aria-hidden="true">×</svg>
</button>
```

### Toggle Button
```html
<button
  aria-pressed="false"
  aria-label="Bold"
  type="button"
>
  <svg aria-hidden="true">B</svg>
</button>
```

### Modal
```html
<div
  role="dialog"
  aria-modal="true"
  aria-labelledby="dialog-title"
  aria-describedby="dialog-desc"
>
  <h2 id="dialog-title">Delete Account</h2>
  <p id="dialog-desc">This action cannot be undone.</p>
  <button type="button">Cancel</button>
  <button type="button">Delete</button>
</div>
```

### Tooltip
```html
<button aria-describedby="tooltip">
  Info
</button>
<div role="tooltip" id="tooltip">
  Additional information
</div>
```

### Loading Spinner
```html
<div
  role="status"
  aria-live="polite"
  aria-label="Loading"
>
  <svg aria-hidden="true"><!-- spinner --></svg>
</div>
```

## Resources

### Guidelines
- [WCAG 2.1](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [Inclusive Components](https://inclusive-components.design/)

### Tools
- [axe DevTools](https://www.deque.com/axe/)
- [WAVE](https://wave.webaim.org/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [Color Oracle](https://colororacle.org/) (colorblind simulator)

### Testing
- [Screen Reader User Survey](https://webaim.org/projects/screenreadersurvey9/)
- [Accessibility Testing Guide](https://www.a11yproject.com/checklist/)

---

**Key Takeaway**: Start with semantic HTML, test with keyboard, verify with screen reader. Accessibility is easier to build in than bolt on later.
