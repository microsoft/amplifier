# Color Strategy Reference

Practical color guidance for frontend work across all stacks. Framework-agnostic principles with stack-specific token examples.

---

## Semantic Color Tokens (required)

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

---

## Dark Mode Strategy

1. **Never invert colors** — use desaturated/lighter tonal variants
2. **Reduce saturation** by 10-20% in dark mode (bright colors are harsh on dark backgrounds)
3. **Elevate with lightness** — higher surfaces are lighter in dark mode (opposite of light mode shadows)
4. **Background hierarchy:** base (darkest) → surface → elevated surface (lightest)
5. **Test contrast separately** — colors that pass in light mode may fail in dark mode
6. **Pure black (#000) is too harsh** — use #0f172a (slate-900) or #18181b (zinc-900) instead

### Dark Mode Elevation Scale

| Level | Light Mode | Dark Mode |
|-------|------------|-----------|
| Base | white | slate-950 |
| Surface | slate-50 | slate-900 |
| Elevated | white + shadow | slate-800 |
| Overlay | white + deeper shadow | slate-700 |

---

## Accessible Color Pairs

All foreground/background combinations must meet WCAG AA:
- **Normal text:** ≥ 4.5:1 contrast ratio
- **Large text (18px+ or 14px bold):** ≥ 3:1
- **UI elements (icons, borders):** ≥ 3:1

### Safe Pairs (pre-validated)

| Foreground | Background | Ratio | Use |
|------------|------------|-------|-----|
| slate-900 | white | 15.4:1 | Body text on light |
| slate-100 | slate-900 | 12.6:1 | Body text on dark |
| white | blue-600 | 6.3:1 | Button text |
| white | red-600 | 4.6:1 | Error button (barely AA) |
| amber-900 | amber-100 | 7.2:1 | Warning badge |
| green-900 | green-100 | 5.8:1 | Success badge |

### Dangerous Pairs (commonly fail)

| Foreground | Background | Ratio | Problem |
|------------|------------|-------|---------|
| gray-400 | white | 2.7:1 | Placeholder text too light |
| red-500 | white | 4.0:1 | Fails AA for normal text |
| blue-400 | white | 3.0:1 | Link color too light |
| white | yellow-500 | 1.9:1 | Yellow buttons unreadable |

---

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

## Anti-Patterns

- **Gray on gray** — muted text on muted background fails contrast
- **Raw hex in components** — always use semantic tokens
- **Color-only meaning** — error states need icon + text, not just red
- **Rainbow dashboards** — use 1-2 accent colors max for data; more = noise
- **Same palette everywhere** — each project deserves intentional color choices
- **Inverting light mode for dark** — produces harsh, unnatural results
- **Red/green only for status** — ~8% of men are colorblind; add icons/shapes
