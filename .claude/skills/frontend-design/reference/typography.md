# Typography

## Classic Typography Principles

### Vertical Rhythm

Your line-height should be the base unit for ALL vertical spacing. If body text has `line-height: 1.5` on `16px` type (= 24px), spacing values should be multiples of 24px. This creates subconscious harmony—text and space share a mathematical foundation.

### Modular Scale & Hierarchy

The common mistake: too many font sizes that are too close together (14px, 15px, 16px, 18px...). This creates muddy hierarchy.

**Use fewer sizes with more contrast.** A 5-size system covers most needs:

| Role | Typical Ratio | Use Case |
|------|---------------|----------|
| xs | 0.75rem | Captions, legal |
| sm | 0.875rem | Secondary UI, metadata |
| base | 1rem | Body text |
| lg | 1.25-1.5rem | Subheadings, lead text |
| xl+ | 2-4rem | Headlines, hero text |

Popular ratios: 1.25 (major third), 1.333 (perfect fourth), 1.5 (perfect fifth). Pick one and commit.

### Readability & Measure

Use `ch` units for character-based measure (`max-width: 65ch`). Line-height scales inversely with line length—narrow columns need tighter leading, wide columns need more.

**Non-obvious**: Increase line-height for light text on dark backgrounds. The perceived weight is lighter, so text needs more breathing room. Add 0.05-0.1 to your normal line-height.

## Font Selection & Pairing

### Choosing Distinctive Fonts

**Avoid the invisible defaults**: Inter, Roboto, Open Sans, Lato, Montserrat. These are everywhere, making your design feel generic. They're fine for documentation or tools where personality isn't the goal—but if you want distinctive design, look elsewhere.

**Better Google Fonts alternatives**:
- Instead of Inter → **Instrument Sans**, **Plus Jakarta Sans**, **Outfit**
- Instead of Roboto → **Onest**, **Figtree**, **Urbanist**
- Instead of Open Sans → **Source Sans 3**, **Nunito Sans**, **DM Sans**
- For editorial/premium feel → **Fraunces**, **Newsreader**, **Lora**

**System fonts are underrated**: `-apple-system, BlinkMacSystemFont, "Segoe UI", system-ui` looks native, loads instantly, and is highly readable. Consider this for apps where performance > personality.

### Pairing Principles

**The non-obvious truth**: You often don't need a second font. One well-chosen font family in multiple weights creates cleaner hierarchy than two competing typefaces. Only add a second font when you need genuine contrast (e.g., display headlines + body serif).

When pairing, contrast on multiple axes:
- Serif + Sans (structure contrast)
- Geometric + Humanist (personality contrast)
- Condensed display + Wide body (proportion contrast)

**Never pair fonts that are similar but not identical** (e.g., two geometric sans-serifs). They create visual tension without clear hierarchy.

### Web Font Loading

The layout shift problem: fonts load late, text reflows, and users see content jump. Here's the fix:

```css
/* 1. Use font-display: swap for visibility */
@font-face {
  font-family: 'CustomFont';
  src: url('font.woff2') format('woff2');
  font-display: swap;
}

/* 2. Match fallback metrics to minimize shift */
@font-face {
  font-family: 'CustomFont-Fallback';
  src: local('Arial');
  size-adjust: 105%;        /* Scale to match x-height */
  ascent-override: 90%;     /* Match ascender height */
  descent-override: 20%;    /* Match descender depth */
  line-gap-override: 10%;   /* Match line spacing */
}

body {
  font-family: 'CustomFont', 'CustomFont-Fallback', sans-serif;
}
```

Tools like [Fontaine](https://github.com/unjs/fontaine) calculate these overrides automatically.

## Modern Web Typography

### Fluid Type

Use `clamp(min, preferred, max)` for fluid typography. The middle value (e.g., `5vw + 1rem`) controls scaling rate—higher vw = faster scaling. Add a rem offset so it doesn't collapse to 0 on small screens.

**When NOT to use fluid type**: Button text, labels, UI elements (should be consistent), very short text, or when you need precise breakpoint control.

### OpenType Features

Most developers don't know these exist. Use them for polish:

```css
/* Tabular numbers for data alignment */
.data-table { font-variant-numeric: tabular-nums; }

/* Proper fractions */
.recipe-amount { font-variant-numeric: diagonal-fractions; }

/* Small caps for abbreviations */
abbr { font-variant-caps: all-small-caps; }

/* Disable ligatures in code */
code { font-variant-ligatures: none; }

/* Enable kerning (usually on by default, but be explicit) */
body { font-kerning: normal; }
```

Check what features your font supports at [Wakamai Fondue](https://wakamaifondue.com/).

## Typography System Architecture

Name tokens semantically (`--text-body`, `--text-heading`), not by value (`--font-size-16`). Include font stacks, size scale, weights, line-heights, and letter-spacing in your token system.

## Accessibility Considerations

Beyond contrast ratios (which are well-documented), consider:

- **Never disable zoom**: `user-scalable=no` breaks accessibility. If your layout breaks at 200% zoom, fix the layout.
- **Use rem/em for font sizes**: This respects user browser settings. Never `px` for body text.
- **Minimum 16px body text**: Smaller than this strains eyes and fails WCAG on mobile.
- **Adequate touch targets**: Text links need padding or line-height that creates 44px+ tap targets.

---

**Avoid**: More than 2-3 font families per project. Skipping fallback font definitions. Ignoring font loading performance (FOUT/FOIT). Using decorative fonts for body text.

## Curated Font Pairings

20 curated pairings for common project types. All fonts available on Google Fonts. Load only the weights you use—typically 400, 500, 600, 700 max.

### Serif + Sans (elegant contrast)

| # | Name | Heading | Body | Mood | Best for |
|---|------|---------|------|------|----------|
| 1 | Classic Elegant | Playfair Display | Inter | Luxury, sophisticated, editorial | Fashion, spa, beauty, magazines |
| 2 | Editorial Modern | Merriweather | Source Sans 3 | Authoritative, readable, warm | News, blogs, publishing, education |
| 3 | Luxury Minimal | Cormorant Garamond | Nunito Sans | Delicate, refined, boutique | Jewelry, wine, art galleries |
| 4 | Heritage Modern | Libre Baskerville | Raleway | Traditional, trustworthy | Law firms, finance, heritage brands |
| 5 | Warm Editorial | Lora | Karla | Warm, inviting, literary | Book sites, cultural, lifestyle |

### Sans + Sans (modern clean)

| # | Name | Heading | Body | Mood | Best for |
|---|------|---------|------|------|----------|
| 6 | Modern Professional | Poppins | Open Sans | Clean, corporate, friendly | SaaS, business apps, startups |
| 7 | Tech Startup | Space Grotesk | DM Sans | Innovative, bold, futuristic | Tech companies, dev tools, AI products |
| 8 | Clean Minimal | Outfit | Work Sans | Minimal, contemporary | Portfolios, design agencies, modern brands |
| 9 | Geometric Bold | Sora | Plus Jakarta Sans | Geometric, confident | Fintech, crypto, modern SaaS |
| 10 | Nordic Clean | Albert Sans | Figtree | Scandinavian, clean | Sustainability, wellness, clean beauty |
| 11 | Friendly Rounded | Nunito | Quicksand | Playful, approachable | Kids apps, social, casual games |
| 12 | Dashboard Pro | IBM Plex Sans | Inter | Professional, data-focused | Dashboards, analytics, enterprise |

### Display + Sans (bold personality)

| # | Name | Heading | Body | Mood | Best for |
|---|------|---------|------|------|----------|
| 13 | Brutalist Type | Anton | Barlow | Raw, bold, urban | Streetwear, music, events |
| 14 | Creative Agency | Clash Display | General Sans | Trendy, artistic | Creative agencies, studios |
| 15 | Festival Energy | Bebas Neue | Montserrat | Energetic, impactful | Sports, events, entertainment |

### Mono + Sans (technical)

| # | Name | Heading | Body | Mood | Best for |
|---|------|---------|------|------|----------|
| 16 | Developer First | JetBrains Mono | Inter | Code-friendly, precise | Dev tools, docs, technical platforms |
| 17 | Hacker Modern | Fira Code | DM Sans | Terminal, modern tech | CLI tools, hacker culture, DevOps |

### Specialty

| # | Name | Heading | Body | Mood | Best for |
|---|------|---------|------|------|----------|
| 18 | Retro Gaming | Press Start 2P | VT323 | Pixel, nostalgic, retro | Gaming, retro apps, pixel art |
| 19 | Handwritten Charm | Caveat | Nunito | Personal, warm, crafty | Personal blogs, handmade, invitations |
| 20 | Art Deco Luxury | Poiret One | Jost | Geometric, glamorous | Fashion, luxury events, premium brands |

### Quick Selection Guide

- **Control panel / admin**: #12 (Dashboard Pro) or #6 (Modern Professional)
- **Landing page**: #7 (Tech Startup) or #8 (Clean Minimal) for modern feel
- **E-commerce**: #1 (Classic Elegant) for luxury, #6 for general
- **Documentation**: #16 (Developer First) or #2 (Editorial Modern)
- **Never use the same pairing across every project** — variety is intentional
