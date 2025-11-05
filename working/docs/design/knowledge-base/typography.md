# Typography for Design Systems

## Fundamentals

### The Basics

**Typography** is the art and technique of arranging type to make written language legible, readable, and appealing.

**Type Anatomy**
- **Baseline**: Line text sits on
- **Cap Height**: Height of capital letters
- **X-Height**: Height of lowercase letters (excluding ascenders/descenders)
- **Ascender**: Part that extends above x-height (b, d, h)
- **Descender**: Part that extends below baseline (g, p, y)
- **Leading**: Vertical space between lines (line-height)
- **Tracking**: Horizontal space between all letters (letter-spacing)
- **Kerning**: Space between specific letter pairs

## Font Classification

### Serif
**Characteristics**: Small decorative strokes at letter endings

**Personality**: Traditional, trustworthy, authoritative, formal

**Use Cases**:
- Long-form content (articles, books)
- Financial/legal institutions
- Luxury brands
- Print materials

**Examples**: Georgia, Times New Roman, Garamond, Merriweather

### Sans-Serif
**Characteristics**: Clean lines without decorative strokes

**Personality**: Modern, clean, approachable, minimal

**Use Cases**:
- UI interfaces
- Digital content
- Tech companies
- Mobile apps

**Examples**: Helvetica, Arial, Inter, Roboto, SF Pro

### Monospace
**Characteristics**: Equal width for all characters

**Personality**: Technical, precise, code-focused

**Use Cases**:
- Code snippets
- Terminal/console output
- Data tables
- Technical documentation

**Examples**: Courier, Monaco, Fira Code, JetBrains Mono

### Display
**Characteristics**: Decorative, attention-grabbing, stylized

**Personality**: Unique, expressive, brand-specific

**Use Cases**:
- Headlines
- Hero sections
- Logos
- Short phrases only (not body text)

**Examples**: Impact, Bebas Neue, Playfair Display

## Type Scale

### The 1.25 (Major Third) Scale
```
12px  → Body small, captions
14px  → Body text, labels (base)
16px  → Body large, default
20px  → H5, small headings
25px  → H4
31px  → H3
39px  → H2
49px  → H1, hero text
61px  → Display text
```

**Ratio**: Each step is 1.25× previous
**Pros**: Balanced, readable, standard
**Cons**: Can feel conservative

### The 1.333 (Perfect Fourth) Scale
```
12px  → Body small
16px  → Body text (base)
21px  → H5
28px  → H4
37px  → H3
50px  → H2
67px  → H1
89px  → Display
```

**Ratio**: Each step is 1.333× previous
**Pros**: More dramatic contrast, modern
**Cons**: Larger jumps can feel aggressive

### The 1.5 (Perfect Fifth) Scale
```
12px  → Body small
16px  → Body (base)
24px  → H5
36px  → H4
54px  → H3
81px  → H2
122px → H1
```

**Ratio**: Each step is 1.5× previous
**Pros**: Strong hierarchy, editorial feel
**Cons**: Large sizes become impractical

### Custom Scale Strategy
1. **Choose base size**: 16px (browser default)
2. **Select ratio**: Based on brand personality
3. **Generate scale**: Use tool like [Type-Scale.com](https://typescale.com)
4. **Round values**: To nearest whole number or 0.5
5. **Test readability**: Ensure comfortable reading at all sizes

## Line Height (Leading)

### Standard Guidelines
| Element | Line Height | Reason |
|---------|-------------|--------|
| Body text (14-18px) | 1.5-1.6 | Optimal readability |
| Large body (18-24px) | 1.4-1.5 | Less space needed at larger sizes |
| Headings | 1.1-1.3 | Tight for impact |
| Display text | 1.0-1.2 | Very tight for drama |
| Buttons/UI | 1.0-1.2 | Compact, centered feel |
| Code | 1.6-1.8 | Extra space for clarity |

### The Formula
```
Line height = Font size × Ratio
```

**Example**: 16px body × 1.5 = 24px line-height

### Unit Choice
```css
/* Good: Relative (scales with font-size) */
line-height: 1.5;

/* Acceptable: Fixed (predictable) */
line-height: 24px;

/* Best: CSS custom property */
--line-height-body: 1.5;
line-height: var(--line-height-body);
```

## Letter Spacing (Tracking)

### Standard Guidelines
| Element | Letter Spacing | Reason |
|---------|---------------|--------|
| Body text | 0 to 0.01em | Natural spacing |
| Small caps | 0.05em to 0.1em | Tighter caps need space |
| Uppercase headings | 0.05em to 0.15em | ALL CAPS feel cramped |
| Display text | -0.02em to -0.05em | Tighter for impact |
| Buttons | 0.01em to 0.05em | Slightly open for legibility |
| Monospace | -0.01em to 0 | Code feels loose by default |

### The Rule
**Smaller text = tighter spacing**
**Larger text = looser spacing (especially uppercase)**

```css
/* Display heading */
h1 {
  font-size: 48px;
  letter-spacing: -0.02em; /* Tighter */
}

/* Button text */
button {
  font-size: 14px;
  text-transform: uppercase;
  letter-spacing: 0.08em; /* Wider */
}
```

## Font Weight

### Standard Weights
| Weight | Name | Use Case |
|--------|------|----------|
| 100 | Thin | Rarely used, fragile |
| 200 | Extra Light | Display text only |
| 300 | Light | Body text (light theme) |
| 400 | Regular | Default body text |
| 500 | Medium | Emphasized body, labels |
| 600 | Semi-Bold | Subheadings, UI elements |
| 700 | Bold | Headings, strong emphasis |
| 800 | Extra Bold | Display, hero text |
| 900 | Black | Rarely used, very heavy |

### Variable Fonts
```css
@font-face {
  font-family: 'Inter';
  font-weight: 100 900;
  src: url('inter-variable.woff2');
}

/* Use any weight 100-900 */
.custom {
  font-weight: 650;
}
```

**Benefits**:
- Single file for all weights
- Smooth weight adjustments
- Better performance

## Responsive Typography

### Fluid Type Scale
```css
/* Scales from 16px (mobile) to 20px (desktop) */
body {
  font-size: clamp(16px, 4vw, 20px);
}

/* Scales from 32px to 64px */
h1 {
  font-size: clamp(32px, 8vw, 64px);
}
```

**Formula**:
```
clamp(min, preferred, max)
```

### Viewport-Based Scale
```css
:root {
  --font-size-base: 16px;
}

@media (min-width: 768px) {
  :root {
    --font-size-base: 18px;
  }
}

@media (min-width: 1024px) {
  :root {
    --font-size-base: 20px;
  }
}
```

### Breakpoint Strategy
| Screen | Base Size | Line Height | Scale Ratio |
|--------|-----------|-------------|-------------|
| Mobile (<640px) | 16px | 1.5 | 1.25 (conservative) |
| Tablet (640-1024px) | 17px | 1.5 | 1.333 |
| Desktop (>1024px) | 18px | 1.6 | 1.333 (more drama) |

## Color & Contrast

### Body Text Contrast
| Background | Text Color | Contrast | WCAG |
|------------|-----------|----------|------|
| White (#FFF) | #000 | 21:1 | AAA+ |
| White (#FFF) | #333 | 12.6:1 | AAA |
| White (#FFF) | #555 | 8.6:1 | AAA |
| White (#FFF) | #767676 | 4.5:1 | AA (minimum) |
| Black (#000) | #FFF | 21:1 | AAA+ |

### Text Color Hierarchy
```css
:root {
  /* Light theme */
  --text-primary: rgba(0, 0, 0, 0.87);   /* Main content */
  --text-secondary: rgba(0, 0, 0, 0.60); /* Supporting text */
  --text-disabled: rgba(0, 0, 0, 0.38);  /* Disabled state */

  /* Dark theme */
  --text-primary-dark: rgba(255, 255, 255, 0.87);
  --text-secondary-dark: rgba(255, 255, 255, 0.60);
  --text-disabled-dark: rgba(255, 255, 255, 0.38);
}
```

## Web Fonts

### Font Loading Strategies

**1. Font-Display**
```css
@font-face {
  font-family: 'Inter';
  src: url('inter.woff2') format('woff2');
  font-display: swap; /* Show fallback first, swap when ready */
}
```

**Options**:
- `swap`: Show fallback immediately, swap when ready (FOUT - Flash of Unstyled Text)
- `block`: Hide text briefly, then show custom font (FOIT - Flash of Invisible Text)
- `fallback`: Compromise between swap and block
- `optional`: Use only if loads quickly, else stick with fallback

**2. Preload Critical Fonts**
```html
<link rel="preload" href="inter-regular.woff2" as="font" type="font/woff2" crossorigin>
```

**3. Self-Host vs CDN**

**Self-Host** (Recommended):
- Faster (same origin)
- Reliable (no external dependency)
- Privacy (no tracking)

**CDN** (Google Fonts):
- Convenience
- Shared cache (obsolete benefit)
- Auto-updates

### Font Stack
```css
body {
  font-family:
    'Inter', /* Custom font */
    -apple-system, /* San Francisco (macOS/iOS) */
    BlinkMacSystemFont, /* San Francisco (macOS Chrome) */
    'Segoe UI', /* Windows */
    'Roboto', /* Android */
    'Helvetica Neue', /* Older macOS */
    Arial, /* Universal fallback */
    sans-serif, /* Generic fallback */
    'Apple Color Emoji', /* Emoji support */
    'Segoe UI Emoji',
    'Segoe UI Symbol';
}
```

### System Font Stack (No Web Fonts)
```css
body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', 'Roboto', 'Oxygen', 'Ubuntu', 'Cantarell', 'Fira Sans', 'Droid Sans', 'Helvetica Neue', sans-serif;
}
```

**Pros**: Instant load, native look, zero cost
**Cons**: Less brand consistency across platforms

## Design Tokens

### Typography Tokens
```css
:root {
  /* Font families */
  --font-family-sans: 'Inter', system-ui, sans-serif;
  --font-family-serif: 'Georgia', serif;
  --font-family-mono: 'Fira Code', monospace;

  /* Font sizes */
  --font-size-xs: 0.75rem;   /* 12px */
  --font-size-sm: 0.875rem;  /* 14px */
  --font-size-base: 1rem;    /* 16px */
  --font-size-lg: 1.125rem;  /* 18px */
  --font-size-xl: 1.25rem;   /* 20px */
  --font-size-2xl: 1.5rem;   /* 24px */
  --font-size-3xl: 1.875rem; /* 30px */
  --font-size-4xl: 2.25rem;  /* 36px */
  --font-size-5xl: 3rem;     /* 48px */

  /* Font weights */
  --font-weight-light: 300;
  --font-weight-normal: 400;
  --font-weight-medium: 500;
  --font-weight-semibold: 600;
  --font-weight-bold: 700;

  /* Line heights */
  --line-height-tight: 1.25;
  --line-height-normal: 1.5;
  --line-height-relaxed: 1.75;

  /* Letter spacing */
  --letter-spacing-tight: -0.02em;
  --letter-spacing-normal: 0;
  --letter-spacing-wide: 0.05em;
}
```

### Semantic Styles
```css
/* Headings */
h1 {
  font-size: var(--font-size-5xl);
  font-weight: var(--font-weight-bold);
  line-height: var(--line-height-tight);
  letter-spacing: var(--letter-spacing-tight);
}

/* Body text */
body {
  font-family: var(--font-family-sans);
  font-size: var(--font-size-base);
  font-weight: var(--font-weight-normal);
  line-height: var(--line-height-normal);
  color: var(--text-primary);
}

/* Code */
code {
  font-family: var(--font-family-mono);
  font-size: 0.9em;
  background: var(--code-bg);
  padding: 0.2em 0.4em;
  border-radius: 3px;
}
```

## Common Patterns

### 1. Measure (Line Length)
**Optimal**: 50-75 characters per line (CPL)
**Acceptable**: 45-90 CPL

```css
.content {
  max-width: 65ch; /* 65 characters */
}
```

**Why**: Prevents eye strain, improves reading speed

### 2. Vertical Rhythm
Consistent spacing based on line-height:

```css
:root {
  --baseline: 1.5rem; /* 24px if base = 16px */
}

p {
  margin-bottom: var(--baseline);
}

h2 {
  margin-top: calc(var(--baseline) * 2);
  margin-bottom: var(--baseline);
}
```

### 3. Text Hierarchy
```css
/* Primary heading */
.heading-1 {
  font-size: 48px;
  font-weight: 700;
  line-height: 1.1;
  letter-spacing: -0.02em;
}

/* Secondary heading */
.heading-2 {
  font-size: 36px;
  font-weight: 600;
  line-height: 1.2;
  letter-spacing: -0.01em;
}

/* Body large */
.body-large {
  font-size: 18px;
  font-weight: 400;
  line-height: 1.6;
}

/* Body default */
.body {
  font-size: 16px;
  font-weight: 400;
  line-height: 1.5;
}

/* Body small */
.body-small {
  font-size: 14px;
  font-weight: 400;
  line-height: 1.5;
  color: var(--text-secondary);
}

/* Caption */
.caption {
  font-size: 12px;
  font-weight: 400;
  line-height: 1.4;
  color: var(--text-secondary);
}
```

### 4. Button Text
```css
.button {
  font-size: 14px;
  font-weight: 600;
  line-height: 1;
  letter-spacing: 0.02em;
  text-transform: uppercase;
}
```

### 5. Input Labels
```css
.label {
  font-size: 14px;
  font-weight: 500;
  line-height: 1.2;
  margin-bottom: 0.5rem;
}
```

## Accessibility

### Text Size
- Minimum: 16px for body text
- Allow user zoom (no `user-scalable=no`)
- Resize to 200% without breaking layout

### Contrast
- Body text: 4.5:1 minimum (AA)
- Large text (18pt+): 3:1 minimum
- Use tools to verify

### Readability
- Short paragraphs (3-4 sentences)
- Bullet points for lists
- Descriptive headings
- Avoid justified text (uneven spacing)
- Avoid ALL CAPS for long text (harder to read)

## Testing Checklist

- [ ] All text sizes render correctly at 200% zoom
- [ ] Line lengths don't exceed 90 characters
- [ ] Text contrast meets WCAG AA (4.5:1)
- [ ] Fonts load within 3 seconds
- [ ] Fallback fonts don't cause layout shift
- [ ] Text is readable on mobile (minimum 16px)
- [ ] Line-height provides comfortable reading
- [ ] Headings have clear hierarchy
- [ ] Links are distinguishable from body text
- [ ] Text is selectable (not rendered as images)

## Best Practices

1. **Limit font families**: 1-2 max (one for UI, one for content)
2. **Use system fonts**: When performance matters
3. **Establish hierarchy**: 3-5 distinct text styles
4. **Test on devices**: Typography looks different on retina vs non-retina
5. **Consider context**: Reading vs scanning vs glancing
6. **Load fonts early**: Preload critical fonts
7. **Provide fallbacks**: Always include generic font families
8. **Use relative units**: `rem` for font-size, `em` for spacing
9. **Optimize web fonts**: Subset fonts, use woff2 format
10. **Test readability**: Real content, not Lorem Ipsum

---

**Key Takeaway**: Good typography is invisible. When done right, users focus on content, not the type itself.
