# Color Intelligence Module

A self-contained, regeneratable module for analyzing color changes using color theory principles. Provides comprehensive analysis of harmony, contrast, semantics, and perception with a 9.5/10 quality baseline.

## Purpose

Analyze color changes to ensure they maintain design quality, accessibility standards, and semantic appropriateness while considering perceptual effects and Swedish aesthetic principles.

## Installation

```bash
npm install @amplified/color-intelligence
```

## Quick Start

```typescript
import { analyzeColor } from '@amplified/color-intelligence';

const input = {
  originalColor: { h: 210, s: 70, l: 50 },
  newColor: { h: 220, s: 65, l: 55 },
  palette: {
    background: { h: 0, s: 0, l: 98 },
    surface: { h: 0, s: 0, l: 100 },
    text: { h: 0, s: 0, l: 10 },
    // ... rest of palette
  },
  context: {
    role: 'primary',
    appliedTo: ['button', 'link'],
    adjacentColors: [{ h: 0, s: 0, l: 100 }],
  }
};

const { analysis, impacts } = analyzeColor(input);

console.log(`Harmony: ${analysis.harmony.type} (${analysis.harmony.quality}/10)`);
console.log(`Contrast: ${analysis.contrast.ratio}:1 (${analysis.contrast.wcagLevel})`);
console.log(`Quality: ${analysis.quality.score}/10`);
```

## Module Contract

### Inputs

```typescript
interface AnalyzerInput {
  originalColor: HSLColor;  // Previous color for comparison
  newColor: HSLColor;       // Color to analyze
  palette: ColorPalette;    // Full design system palette
  context: UsageContext;    // Where/how color is used
}
```

### Outputs

```typescript
interface AnalyzerOutput {
  analysis: ColorAnalysis;  // Complete analysis results
  impacts: ImpactReport[];  // Issues and recommendations
}
```

### Key Analysis Functions

#### 1. `calculateHarmony()`
Determines color relationships based on color wheel positions:
- **Complementary**: 180° apart (high contrast, vibrant)
- **Analogous**: 30-60° apart (harmonious, calm)
- **Triadic**: 120° apart (balanced, dynamic)
- **Monochromatic**: Same hue (unified, sophisticated)

#### 2. `validateContrast()`
WCAG accessibility validation:
- **Formula**: `L = 0.2126*R + 0.7152*G + 0.0722*B`
- **Ratio**: `(L1 + 0.05) / (L2 + 0.05)`
- **Requirements**:
  - Text: 4.5:1 (AA), 7:1 (AAA)
  - UI Components: 3:1 (AA), 4.5:1 (AAA)

#### 3. `assessSemantics()`
Validates color fits its semantic role:
- **Success**: Green (120°), S: 60-70%, L: 45-55%
- **Warning**: Orange (40°), S: 80-90%, L: 50-60%
- **Error**: Red (0°), S: 65-75%, L: 50-60%
- **Info**: Blue (210°), S: 60-70%, L: 50-60%

#### 4. `predictPerception()`
Context-dependent appearance (Albers principle):
- Simultaneous contrast effects
- Adjacent color influence
- Perceptual shift calculations

## Quality Metrics

The module evaluates colors across multiple dimensions:

```typescript
interface QualityMetrics {
  score: number;              // Overall quality (0-10)
  refinement: number;         // Subtlety/sophistication
  vibrancy: number;          // Color intensity
  balance: number;           // Compositional harmony
  aestheticAlignment: number; // Swedish aesthetic fit
}
```

### Swedish Aesthetic Principles
- **Saturation**: 15-70% (ideal: 40%)
- **Lightness**: 20-90% (ideal: 60%)
- **Refinement**: Subtle over bold
- **Quality target**: 9.5/10

## Performance Characteristics

- **Time complexity**: O(n) for n palette colors
- **Execution time**: <5ms for full analysis
- **Memory usage**: ~10KB per analysis
- **Zero external dependencies** for core calculations

## Error Handling

| Error Type | Condition | Recovery |
|------------|-----------|----------|
| Invalid HSL | Values out of range | Clamp to valid range |
| Missing context | No adjacent colors | Use defaults |
| Performance | >5ms execution | Log warning, continue |

## Configuration

The module uses predefined constants that can be imported for customization:

```typescript
import {
  WCAG_REQUIREMENTS,
  SEMANTIC_HUE_RANGES,
  SWEDISH_AESTHETIC
} from '@amplified/color-intelligence/constants';
```

## Testing

```bash
# Run tests
npm test

# Type checking
npm run typecheck

# Linting
npm run lint
```

## Examples

### Analyzing a Primary Button Color

```typescript
const buttonAnalysis = analyzeColor({
  originalColor: { h: 210, s: 70, l: 50 },
  newColor: { h: 220, s: 75, l: 45 },
  palette: defaultPalette,
  context: {
    role: 'accent',
    appliedTo: ['primary-button', 'cta'],
    adjacentColors: [
      { h: 0, s: 0, l: 100 }, // White background
    ],
  },
});

if (buttonAnalysis.impacts.some(i => i.severity === 'critical')) {
  console.error('Critical accessibility issues found');
}
```

### Validating Semantic Colors

```typescript
const errorColorAnalysis = analyzeColor({
  originalColor: { h: 0, s: 70, l: 50 },
  newColor: { h: 15, s: 65, l: 55 }, // Slightly orange
  palette: defaultPalette,
  context: {
    role: 'semantic',
    appliedTo: ['error-message', 'validation-error'],
    adjacentColors: [],
  },
});

if (!errorColorAnalysis.analysis.semantics.fitsRole) {
  console.warn('Color may not convey error effectively');
}
```

## API Reference

See the exported types and functions in `index.ts` for the complete API.

## Regeneration Specification

This module can be fully regenerated from this specification. Key invariants:

- HSL color space for all calculations
- WCAG 2.1 contrast formulas
- Color wheel harmony angles
- Swedish aesthetic preferences
- <5ms performance target

## Contributing

When modifying this module:
1. Maintain pure functions without side effects
2. Keep all calculations mathematically accurate
3. Preserve the <5ms performance target
4. Update types for any new functionality
5. Maintain 9.5/10 quality baseline

## License

MIT