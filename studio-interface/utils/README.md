# CSSVariableInjector Module

## Purpose
Real-time CSS variable management with preview capabilities and validation.

## Contract

### Input
- HSL color objects to inject
- CSS variable tokens to validate
- Preview/revert commands

### Output
- CSS variables updated in document
- Validation results for tokens
- Preview styles with high specificity

### Side Effects
- Modifies document.documentElement.style
- Creates/removes preview stylesheet
- Uses requestAnimationFrame for batching

## Public Interface

```typescript
// Core functions
injectVariables(updates)      // Apply CSS variables
previewVariables(updates)     // Non-destructive preview
revertPreview()              // Cancel preview
validateTokens(tokens)       // Check token existence

// Utilities
hslToCSS(color)             // HSL object to CSS string
getCurrentValue(token)       // Read current CSS value
batchInject(updates)        // Efficient bulk updates
debugLogVariables()         // Development helper
```

## Usage

```typescript
import { injectVariables, previewVariables, revertPreview } from './utils/cssInjector';

// Direct injection
injectVariables([
  { token: '--background', value: { h: 220, s: 15, l: 18 } }
]);

// Preview mode
previewVariables([
  { token: '--primary', value: { h: 210, s: 70, l: 50 } }
]);

// Cancel preview
revertPreview();
```

## Performance Characteristics
- Batched updates via requestAnimationFrame
- Single DOM write per frame (16ms)
- Preview uses high-specificity stylesheet
- No memory leaks (cleanup on revert)

## Error Handling
- Out-of-range HSL values are clamped
- Invalid tokens logged but don't throw
- CORS-restricted stylesheets skipped
- Graceful fallback for SSR

## Browser Compatibility
- Modern browsers with CSS Variables support
- Graceful degradation for SSR
- Works with Shadow DOM

## Regeneration Specification
This module can be fully regenerated from this specification. Key invariants:
- HSL to CSS conversion format
- Preview stylesheet ID: 'color-preview-styles'
- Batch updates via requestAnimationFrame
- Token validation checks computed styles first
- High specificity preview with :root:root