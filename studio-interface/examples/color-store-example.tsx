/**
 * ColorStore Integration Example
 *
 * Demonstrates how to use ColorStore and CSSVariableInjector together
 * for real-time color management in the Studio interface.
 */

'use client';

import { useEffect } from 'react';
import { useColorStore } from '../state/colorStore';
import type { HSLColor } from '../../packages/color-intelligence/types';

/**
 * Example: Color Control Panel
 *
 * Shows how to build a color control interface that:
 * - Updates colors in real-time
 * - Supports preview on hover
 * - Has undo/redo functionality
 * - Persists changes to localStorage
 */
export function ColorControlPanel() {
  const store = useColorStore();

  // Initialize from CSS on mount
  useEffect(() => {
    store.initializeFromCSS();
  }, []);

  // Example 1: Update a color with history tracking
  const handleColorUpdate = () => {
    const newPrimary: HSLColor = { h: 210, s: 70, l: 50 };
    store.updateColor('primary', newPrimary, 'Changed primary to blue');
  };

  // Example 2: Preview a color without committing
  const handlePreview = () => {
    const previewColor: HSLColor = { h: 160, s: 60, l: 45 };
    store.previewColorChange('accent', previewColor);
  };

  // Example 3: Batch update multiple colors
  const handleThemeChange = () => {
    store.batchUpdateColors([
      { token: 'background', color: { h: 220, s: 15, l: 8 } },
      { token: 'surface', color: { h: 220, s: 15, l: 12 } },
      { token: 'text', color: { h: 220, s: 10, l: 95 } },
    ], 'Applied dark theme');
  };

  // Example 4: Apply a suggestion from the AI
  const handleApplySuggestion = () => {
    // Assuming we have suggestions from the color intelligence engine
    if (store.suggestions.length > 0) {
      store.applySuggestion(store.suggestions[0].id);
    }
  };

  return (
    <div className="color-control-panel">
      {/* Undo/Redo Controls */}
      <div className="history-controls">
        <button onClick={store.undo} disabled={!store.canUndo()}>
          Undo
        </button>
        <button onClick={store.redo} disabled={!store.canRedo()}>
          Redo
        </button>
      </div>

      {/* Color Actions */}
      <div className="color-actions">
        <button onClick={handleColorUpdate}>
          Update Primary Color
        </button>

        <button
          onMouseEnter={handlePreview}
          onMouseLeave={store.clearPreview}
        >
          Preview Accent (Hover)
        </button>

        <button onClick={handleThemeChange}>
          Apply Dark Theme
        </button>
      </div>

      {/* Current Colors Display */}
      <div className="current-colors">
        {Object.entries(store.colors).map(([token, color]) => (
          <div key={token} className="color-item">
            <span>{token}:</span>
            <span>hsl({color.h}, {color.s}%, {color.l}%)</span>
            <div
              style={{
                width: 20,
                height: 20,
                backgroundColor: `hsl(${color.h}, ${color.s}%, ${color.l}%)`,
                border: '1px solid var(--border)'
              }}
            />
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Example: Color Picker Integration
 *
 * Shows how to integrate with a color picker component
 */
export function ColorPickerExample() {
  const { updateColor, previewColorChange, clearPreview } = useColorStore();

  const handleColorChange = (token: keyof typeof useColorStore, hsl: HSLColor) => {
    // While dragging/adjusting: preview
    previewColorChange(token, hsl);
  };

  const handleColorCommit = (token: keyof typeof useColorStore, hsl: HSLColor) => {
    // On release/commit: update
    clearPreview();
    updateColor(token, hsl, `Adjusted ${token} color`);
  };

  // Your color picker component would call these handlers
  return null;
}

/**
 * Example: Using CSSVariableInjector Directly
 *
 * For advanced use cases where you need direct control
 */
import { injectVariables, previewVariables, revertPreview, validateTokens } from '../utils/cssInjector';

export function DirectInjectionExample() {
  // Example 1: Direct injection
  const applyCustomColors = () => {
    injectVariables([
      { token: '--custom-color-1', value: { h: 45, s: 80, l: 60 } },
      { token: '--custom-color-2', value: { h: 180, s: 50, l: 40 } },
    ]);
  };

  // Example 2: Validate before injection
  const safeInject = () => {
    const tokens = ['--background', '--invalid-token'];
    const validation = validateTokens(tokens);

    if (validation.invalid.length > 0) {
      console.warn('Invalid tokens:', validation.invalid);
      console.warn('Errors:', validation.errors);
    }

    // Only inject valid tokens
    validation.valid.forEach(token => {
      injectVariables([
        { token, value: { h: 0, s: 0, l: 50 } }
      ]);
    });
  };

  // Example 3: Preview mode
  const startPreview = () => {
    previewVariables([
      { token: '--background', value: { h: 0, s: 100, l: 50 } } // Red background preview
    ]);

    // Revert after 3 seconds
    setTimeout(() => {
      revertPreview();
    }, 3000);
  };

  return null;
}

/**
 * Example: Listening to Color Changes
 *
 * Components can subscribe to color changes
 */
export function ColorSubscriberExample() {
  const colors = useColorStore(state => state.colors);
  const primaryColor = useColorStore(state => state.colors.primary);

  useEffect(() => {
    console.log('Colors changed:', colors);
  }, [colors]);

  useEffect(() => {
    console.log('Primary color changed:', primaryColor);
    // Update dependent calculations, trigger animations, etc.
  }, [primaryColor]);

  return (
    <div style={{ color: `hsl(${primaryColor.h}, ${primaryColor.s}%, ${primaryColor.l}%)` }}>
      This text uses the primary color
    </div>
  );
}

/**
 * Example: Integration with Color Intelligence
 *
 * Shows how ColorStore works with the color intelligence engine
 */
export async function ColorIntelligenceIntegration() {
  const store = useColorStore.getState();

  // When user changes a color, get suggestions
  const handleColorChange = async (token: string, newColor: HSLColor) => {
    // Update the color
    store.updateColor(token as any, newColor);

    // Get suggestions from color intelligence (pseudo-code)
    // const suggestions = await colorIntelligence.getSuggestions({
    //   currentPalette: store.colors,
    //   changedToken: token,
    //   changedColor: newColor,
    //   intent: { goal: 'harmonize', magnitude: 'subtle' }
    // });

    // store.setSuggestions(suggestions);
  };
}