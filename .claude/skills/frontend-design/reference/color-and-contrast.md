# Color & Contrast

## Color Spaces: Use OKLCH

**Stop using HSL.** Use OKLCH (or LCH) instead. It's perceptually uniform, meaning equal steps in lightness *look* equal—unlike HSL where 50% lightness in yellow looks bright while 50% in blue looks dark.

```css
/* OKLCH: lightness (0-100%), chroma (0-0.4+), hue (0-360) */
--color-primary: oklch(60% 0.15 250);      /* Blue */
--color-primary-light: oklch(85% 0.08 250); /* Same hue, lighter */
--color-primary-dark: oklch(35% 0.12 250);  /* Same hue, darker */
```

**Key insight**: As you move toward white or black, reduce chroma (saturation). High chroma at extreme lightness looks garish. A light blue at 85% lightness needs ~0.08 chroma, not the 0.15 of your base color.

## Building Functional Palettes

### The Tinted Neutral Trap

**Pure gray is dead.** Add a subtle hint of your brand hue to all neutrals:

```css
/* Dead grays */
--gray-100: oklch(95% 0 0);     /* No personality */
--gray-900: oklch(15% 0 0);

/* Warm-tinted grays (add brand warmth) */
--gray-100: oklch(95% 0.01 60);  /* Hint of warmth */
--gray-900: oklch(15% 0.01 60);

/* Cool-tinted grays (tech, professional) */
--gray-100: oklch(95% 0.01 250); /* Hint of blue */
--gray-900: oklch(15% 0.01 250);
```

The chroma is tiny (0.01) but perceptible. It creates subconscious cohesion between your brand color and your UI.

### Palette Structure

A complete system needs:

| Role | Purpose | Example |
|------|---------|---------|
| **Primary** | Brand, CTAs, key actions | 1 color, 3-5 shades |
| **Neutral** | Text, backgrounds, borders | 9-11 shade scale |
| **Semantic** | Success, error, warning, info | 4 colors, 2-3 shades each |
| **Surface** | Cards, modals, overlays | 2-3 elevation levels |

**Skip secondary/tertiary unless you need them.** Most apps work fine with one accent color. Adding more creates decision fatigue and visual noise.

### The 60-30-10 Rule (Applied Correctly)

This rule is about **visual weight**, not pixel count:

- **60%**: Neutral backgrounds, white space, base surfaces
- **30%**: Secondary colors—text, borders, inactive states
- **10%**: Accent—CTAs, highlights, focus states

The common mistake: using the accent color everywhere because it's "the brand color." Accent colors work *because* they're rare. Overuse kills their power.

## Semantic Color Tokens

Never use raw hex in components. Define semantic tokens that map to purpose:

| Token | Purpose | Light Mode | Dark Mode |
|-------|---------|------------|-----------|
| `primary` | Main brand action | Bold, saturated | Slightly desaturated |
| `secondary` | Supporting action | Muted variant | Lighter tonal variant |
| `accent` | Highlight, badge, link | Vibrant contrast | Same hue, lighter |
| `background` | Page/card background | White or near-white | Dark gray (not pure black) |
| `surface` | Cards, elevated areas | Slightly off-white | Slightly lighter than bg |
| `foreground` | Primary text | Dark (slate-900) | Light (slate-100) |
| `muted` | Secondary text, borders | Gray-500 | Gray-400 |
| `destructive` | Delete, error | Red-600 | Red-400 |
| `success` | Confirmation | Green-600 | Green-400 |
| `warning` | Caution | Amber-600 | Amber-400 |

### Token Hierarchy

Use two layers: primitive tokens (`--blue-500`) and semantic tokens (`--color-primary: var(--blue-500)`). For dark mode, only redefine the semantic layer—primitives stay the same.

### Stack Examples

**Tailwind CSS / shadcn:**
```css
@layer base {
  :root {
    --primary: 222.2 47.4% 11.2%;
    --primary-foreground: 210 40% 98%;
    --destructive: 0 84.2% 60.2%;
    --muted: 210 40% 96.1%;
  }
  .dark {
    --primary: 210 40% 98%;
    --primary-foreground: 222.2 47.4% 11.2%;
    --destructive: 0 62.8% 30.6%;
    --muted: 217.2 32.6% 17.5%;
  }
}
```

**Blazor / CSS variables:**
```css
:root {
  --color-primary: #1e40af;
  --color-on-primary: #ffffff;
  --color-destructive: #dc2626;
  --color-surface: #f8fafc;
}
[data-theme="dark"] {
  --color-primary: #93c5fd;
  --color-on-primary: #1e293b;
  --color-destructive: #f87171;
  --color-surface: #1e293b;
}
```

## Contrast & Accessibility

### WCAG Requirements

| Content Type | AA Minimum | AAA Target |
|--------------|------------|------------|
| Body text | 4.5:1 | 7:1 |
| Large text (18px+ or 14px bold) | 3:1 | 4.5:1 |
| UI components, icons | 3:1 | 4.5:1 |
| Non-essential decorations | None | None |

**The gotcha**: Placeholder text still needs 4.5:1. That light gray placeholder you see everywhere? Usually fails WCAG.

### Safe Pairs (pre-validated)

| Foreground | Background | Ratio | Use |
|------------|------------|-------|-----|
| slate-900 | white | 15.4:1 | Body text on light |
| slate-100 | slate-900 | 12.6:1 | Body text on dark |
| white | blue-600 | 6.3:1 | Button text |
| white | red-600 | 4.6:1 | Error button (barely AA) |
| amber-900 | amber-100 | 7.2:1 | Warning badge |
| green-900 | green-100 | 5.8:1 | Success badge |

### Dangerous Color Combinations

These commonly fail contrast or cause readability issues:

- Light gray text on white (the #1 accessibility fail)
- **Gray text on any colored background**—gray looks washed out and dead on color. Use a darker shade of the background color, or transparency
- Red text on green background (or vice versa)—8% of men can't distinguish these
- Blue text on red background (vibrates visually)
- Yellow text on white (almost always fails)
- Thin light text on images (unpredictable contrast)

| Foreground | Background | Ratio | Problem |
|------------|------------|-------|---------|
| gray-400 | white | 2.7:1 | Placeholder text too light |
| red-500 | white | 4.0:1 | Fails AA for normal text |
| blue-400 | white | 3.0:1 | Link color too light |
| white | yellow-500 | 1.9:1 | Yellow buttons unreadable |

### Never Use Pure Gray or Pure Black

Pure gray (`oklch(50% 0 0)`) and pure black (`#000`) don't exist in nature—real shadows and surfaces always have a color cast. Even a chroma of 0.005-0.01 is enough to feel natural without being obviously tinted.

### Testing

Don't trust your eyes. Use tools:

- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- Browser DevTools → Rendering → Emulate vision deficiencies
- [Polypane](https://polypane.app/) for real-time testing

## Theming: Light & Dark Mode

### Dark Mode Is Not Inverted Light Mode

You can't just swap colors. Dark mode requires different design decisions:

| Light Mode | Dark Mode |
|------------|-----------|
| Shadows for depth | Lighter surfaces for depth (no shadows) |
| Dark text on light | Light text on dark (reduce font weight) |
| Vibrant accents | Desaturate accents slightly |
| White backgrounds | Never pure black—use dark gray (oklch 12-18%) |

```css
/* Dark mode depth via surface color, not shadow */
:root[data-theme="dark"] {
  --surface-1: oklch(15% 0.01 250);
  --surface-2: oklch(20% 0.01 250);  /* "Higher" = lighter */
  --surface-3: oklch(25% 0.01 250);

  /* Reduce text weight slightly */
  --body-weight: 350;  /* Instead of 400 */
}
```

### Dark Mode Elevation Scale

| Level | Light Mode | Dark Mode |
|-------|------------|-----------|
| Base | white | slate-950 |
| Surface | slate-50 | slate-900 |
| Elevated | white + shadow | slate-800 |
| Overlay | white + deeper shadow | slate-700 |

**Strategy rules:**
1. Never invert colors—use desaturated/lighter tonal variants
2. Reduce saturation by 10-20% in dark mode (bright colors are harsh on dark backgrounds)
3. Elevate with lightness—higher surfaces are lighter in dark mode (opposite of light mode shadows)
4. Test contrast separately—colors that pass in light mode may fail in dark mode
5. Pure black (#000) is too harsh—use #0f172a (slate-900) or #18181b (zinc-900) instead

## Alpha Is A Design Smell

Heavy use of transparency (rgba, hsla) usually means an incomplete palette. Alpha creates unpredictable contrast, performance overhead, and inconsistency. Define explicit overlay colors for each context instead. Exception: focus rings and interactive states where see-through is needed.

## Color by Product Type

| Product Type | Primary Direction | Mood | Avoid |
|---|---|---|---|
| **SaaS / Dashboard** | Blue, indigo, violet | Trust, professional | Overly playful palettes |
| **E-commerce** | Brand-specific + neutral | Conversion-focused, content takes center stage | Competing with product images |
| **Health / Medical** | Teal, green, blue | Calm, trustworthy, clinical | Red as primary (= danger) |
| **Finance / Fintech** | Navy, dark blue, green | Stability, growth | Bright/playful colors |
| **Creative / Design** | Bold, any direction | Distinctive, memorable | Generic corporate blue |
| **Education** | Warm blue, orange, green | Approachable, encouraging | Dark/intimidating palettes |
| **Admin Panel** | Neutral gray + accent | Functional, unobtrusive | Heavy use of color (data takes priority) |

---

**Avoid**: Relying on color alone to convey information. Raw hex in components—always use semantic tokens. Creating palettes without clear roles for each color. Using pure black (#000) for large areas. Skipping color blindness testing (8% of men affected). Gray on gray—muted text on muted background fails contrast. Rainbow dashboards—use 1-2 accent colors max for data; more = noise. Inverting light mode for dark—produces harsh, unnatural results. Red/green only for status—add icons/shapes for colorblind users.
