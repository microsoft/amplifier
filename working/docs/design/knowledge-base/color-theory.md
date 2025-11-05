# Color Theory for Design Systems

## Core Principles

### 1. Hue, Saturation, Lightness (HSL)
- **Hue**: The color itself (0-360°)
- **Saturation**: Color intensity (0-100%)
- **Lightness**: Light to dark (0-100%)

### 2. Color Harmony

#### Complementary Colors
Colors opposite on the color wheel create maximum contrast and vibrancy.
- Red (0°) ↔ Cyan (180°)
- Blue (240°) ↔ Yellow (60°)
- Green (120°) ↔ Magenta (300°)

#### Analogous Colors
Adjacent colors (30-60° apart) create harmonious, cohesive palettes.
- Blue (240°) → Blue-Green (210°) → Green (180°)

#### Triadic Colors
Three colors equally spaced (120° apart) create balanced, vibrant schemes.
- Red (0°) → Green (120°) → Blue (240°)

### 3. Contrast & Accessibility

#### WCAG Guidelines
- **AA Standard**: 4.5:1 contrast ratio for normal text
- **AAA Standard**: 7:1 contrast ratio for normal text
- **Large Text**: 3:1 minimum (18pt+ or 14pt+ bold)

#### Calculating Contrast
Use relative luminance formula:
```
L = 0.2126 * R + 0.7152 * G + 0.0722 * B
Contrast = (L1 + 0.05) / (L2 + 0.05)
```

### 4. Perceptual Foundations

#### Context-Dependent Perception (Albers)

**Josef Albers' Key Insight**: "In visual perception a color is almost never seen as it really is—as it physically is."

Color perception is **radically contextual**. The same hex value appears different depending on:
- **Surrounding colors**: A gray square looks darker on white, lighter on black
- **Adjacent hues**: Colors influence each other (simultaneous contrast)
- **Size and proportion**: Small areas vs large areas of the same color
- **Lighting conditions**: Daylight vs artificial light transforms appearance

**Practical Application**:
- Never judge colors in isolation—always preview in context
- Test button colors against actual background colors
- A color that "looks good" in Figma may fail on the real page
- This is why our Quality Guardian validates colors **in context**, not just mathematically

#### Itten's Seven Color Contrasts

Johannes Itten identified seven types of contrast that make colors work together:

1. **Hue Contrast**: Different colors (red vs blue vs yellow)
2. **Light-Dark Contrast**: Value differences (white vs black)
3. **Cold-Warm Contrast**: Temperature differences (blue vs orange)
4. **Complementary Contrast**: Opposite colors (red vs cyan)
5. **Simultaneous Contrast**: Colors creating afterimages
6. **Saturation Contrast**: Pure vs muted colors
7. **Extension Contrast**: Proportion of color areas

**Practical Application**:
- Our Ghost Slide variant uses **hue contrast** (purple) + **light-dark contrast** (white text)
- Magnetic variant uses **complementary contrast** for visual interest
- These aren't aesthetic choices—they're perceptual strategies for clarity

#### Why WCAG Contrast Ratios Work

**The Science**: WCAG's 4.5:1 ratio isn't arbitrary—it's based on empirical research with users who have low vision.

**The Research**:
- Tested with people having 20/40 vision (common age-related decline)
- Accounts for color perception variations
- Ensures readability under different lighting conditions
- Validated across different screen technologies

**The Reality**:
- **4.5:1** = usable by 99% of users with low vision (Level AA)
- **7:1** = maximum accessibility (Level AAA)
- Below 3:1 = unusable for many people, not just a "guideline"

**Cultural Context**: While contrast ratios are universal (based on human vision), color **meanings** vary:
- **Red**: Danger in the West, luck in China, purity in India
- **White**: Purity in the West, death/mourning in parts of Asia
- **Blue**: Generally trustworthy across cultures (one of the few universal associations)

Our system provides the perceptual foundation (contrast) while leaving cultural interpretation to you.

### 5. Color Psychology

#### Warm Colors (Red, Orange, Yellow)
- **Energy**: High stimulation, urgency, excitement
- **Use Cases**: CTAs, warnings, promotional content
- **Caution**: Can feel aggressive if overused

#### Cool Colors (Blue, Green, Purple)
- **Calm**: Trust, stability, professionalism
- **Use Cases**: Primary interfaces, backgrounds, corporate
- **Caution**: Can feel cold or distant

#### Neutrals (Gray, Black, White, Beige)
- **Balance**: Foundation, readability, sophistication
- **Use Cases**: Text, backgrounds, borders
- **Caution**: Can feel boring without accent colors

## Design System Application

### 1. Color Scales (10-point scale)

#### Creating Consistent Scales
```
50:  Lightest tint (backgrounds)
100: Very light (hover states)
200: Light (borders)
300: Medium-light (disabled states)
400: Medium (secondary text)
500: Base color (brand color)
600: Medium-dark (hover states)
700: Dark (primary text)
800: Very dark (emphasis)
900: Darkest shade (headings)
```

#### Perceptual Uniformity
Ensure each step feels equally spaced:
- Use HSL/Lab color spaces for consistent lightness
- Test with colorblind simulation
- Validate contrast ratios between adjacent steps

### 2. Semantic Color Roles

#### Status Colors
- **Success**: Green (120°), S: 60-70%, L: 45-55%
- **Warning**: Yellow/Orange (30-45°), S: 80-90%, L: 50-60%
- **Error**: Red (0-10°), S: 65-75%, L: 50-60%
- **Info**: Blue (200-220°), S: 60-70%, L: 50-60%

#### Interaction Colors
- **Primary**: Brand color (consistent hue)
- **Secondary**: Complementary or analogous to primary
- **Hover**: 5-10% darker (L: -5 to -10)
- **Active**: 10-15% darker (L: -10 to -15)
- **Disabled**: Desaturated (S: 10-20%, L: 70-80%)

### 3. Dark Mode Considerations

#### Inversion Strategy
Don't simply invert colors:
- Reduce saturation in dark mode (S: -10 to -20%)
- Adjust lightness curves (darker backgrounds, lighter text)
- Maintain contrast ratios

#### Color Temperature
- Warm up dark backgrounds slightly (add subtle yellow/red)
- Cool down light text slightly (add subtle blue)
- Prevents eye strain in low-light conditions

### 4. Color Systems

#### Monochromatic
Single hue with varying saturation/lightness:
- **Pros**: Cohesive, elegant, timeless
- **Cons**: Can lack visual hierarchy
- **Use**: Minimalist designs, luxury brands

#### Duotone
Two contrasting colors:
- **Pros**: Strong identity, clear hierarchy
- **Cons**: Limited flexibility
- **Use**: Marketing sites, portfolios

#### Polychromatic
Multiple colors from color wheel:
- **Pros**: Vibrant, expressive, flexible
- **Cons**: Requires careful balance
- **Use**: Complex apps, creative platforms

## Best Practices

### 1. Start with Purpose
- Define brand personality first
- Choose primary color based on industry/emotion
- Build system around that foundation

### 2. Test in Context
- View colors on different screens (retina, non-retina)
- Test under different lighting (daylight, artificial)
- Simulate colorblindness (protanopia, deuteranopia, tritanopia)

### 3. Document Decisions
- Explain color choices (not just hex values)
- Provide usage guidelines (when to use each color)
- Include accessibility requirements

### 4. Maintain Consistency
- Use color tokens (variables/CSS custom properties)
- Lock down brand colors (don't tweak without process)
- Allow flexibility in neutrals/utilities

## Common Mistakes to Avoid

1. **Too Many Colors**: Limit to 5-7 primary colors max
2. **Low Contrast**: Always test against WCAG standards
3. **Ignoring Context**: Colors look different on white vs dark backgrounds
4. **Trend-Chasing**: Choose timeless colors over trendy ones
5. **No System**: Random colors instead of calculated scales

## Tools & Resources

- **Color Scale Generators**: Leonardo, ColorBox, Chroma.js
- **Contrast Checkers**: WebAIM, Stark, Accessible Colors
- **Inspiration**: Coolors, Adobe Color, Huetone
- **Testing**: Color Oracle (colorblind simulator)

---

**Key Takeaway**: Color is a science AND an art. Use theory to guide decisions, but trust your eye for the final polish.
