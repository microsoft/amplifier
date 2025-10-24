# ColorStore Module

## Purpose
Centralized color state management with undo/redo, preview capabilities, and real-time CSS synchronization.

## Contract

### Input
- HSL color values for any design token
- Color suggestions from the intelligence engine
- Preview requests for non-destructive testing

### Output
- Updated color palette state
- CSS variable updates (via CSSVariableInjector)
- History for undo/redo operations
- localStorage persistence

### Side Effects
- Updates CSS variables in real-time
- Persists color palette to localStorage
- Maintains history stack in memory

## Public Interface

```typescript
// Core functions
updateColor(token, color, description?) // Commit a color change
previewColorChange(token, color)         // Preview without committing
clearPreview()                            // Cancel preview
undo() / redo()                          // Navigate history
applySuggestion(suggestionId)           // Apply AI suggestion
batchUpdateColors(changes, description)  // Multiple changes as one transaction

// State
colors: ColorPalette                     // Current palette
suggestions: ColorSuggestion[]           // Available suggestions
history: ColorHistoryEntry[]             // Change history
```

## Usage

```typescript
import { useColorStore } from './state/colorStore';

// In a component
const store = useColorStore();
store.updateColor('primary', { h: 210, s: 70, l: 50 });

// Preview on hover
onMouseEnter={() => store.previewColorChange('accent', newColor))
onMouseLeave={() => store.clearPreview())
```

## Error Handling
- Invalid color values are clamped to valid ranges
- Missing CSS variables use fallback values
- localStorage failures are logged but don't crash

## Performance
- < 16ms for state updates (React 18 batching)
- CSS updates via requestAnimationFrame
- History limited to prevent memory issues

## Regeneration Specification
This module can be fully regenerated from this specification. Key invariants:
- Zustand store structure
- TOKEN_MAP for CSS variable mapping
- History tracking with undo/redo
- Preview state management
- localStorage key: 'colorPalette'