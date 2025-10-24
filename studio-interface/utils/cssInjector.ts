/**
 * CSSVariableInjector - Real-time CSS Variable Management
 *
 * A self-contained module for injecting and managing CSS variables
 * with preview capabilities and validation.
 *
 * Contract:
 * - Converts HSL colors to CSS format and injects into document
 * - Supports non-destructive preview mode with high specificity
 * - Validates token existence before injection
 * - Optimized for 60fps performance with requestAnimationFrame
 *
 * @module CSSVariableInjector
 */

import type { HSLColor } from '../../packages/color-intelligence/types';

/**
 * CSS variable update structure
 */
export interface VariableUpdate {
  /** CSS variable name (e.g., '--background') */
  token: string;
  /** HSL color value to apply */
  value: HSLColor;
}

/**
 * Token validation result
 */
export interface ValidationResult {
  /** Valid token names */
  valid: string[];
  /** Invalid token names */
  invalid: string[];
  /** Error messages for invalid tokens */
  errors: Map<string, string>;
}

/**
 * Cached original values for reverting preview
 */
interface PreviewCache {
  /** Map of token to original value */
  originalValues: Map<string, string>;
  /** Preview stylesheet element */
  styleElement: HTMLStyleElement | null;
  /** Currently previewing tokens */
  activeTokens: Set<string>;
}

/**
 * Performance optimization: batch updates
 */
interface UpdateBatch {
  /** Pending updates */
  updates: Map<string, HSLColor>;
  /** Animation frame ID */
  frameId: number | null;
}

/**
 * Preview cache singleton
 */
const previewCache: PreviewCache = {
  originalValues: new Map(),
  styleElement: null,
  activeTokens: new Set()
};

/**
 * Update batch singleton
 */
const updateBatch: UpdateBatch = {
  updates: new Map(),
  frameId: null
};

/**
 * Convert HSL color object to CSS string
 *
 * @param color - HSL color object (s and l as decimals 0-1)
 * @returns CSS-formatted HSL string
 *
 * @example
 * hslToCSS({ h: 220, s: 0.15, l: 0.18 }) // "hsl(220, 15%, 18%)"
 * hslToCSS({ h: 220, s: 0.15, l: 0.18, a: 0.5 }) // "hsl(220, 15%, 18%, 0.5)"
 */
export function hslToCSS(color: HSLColor): string {
  const { h, s, l, a } = color;

  // Convert s and l from decimal (0-1) to percentage
  const sPercent = s * 100;
  const lPercent = l * 100;

  // Validate ranges
  if (h < 0 || h > 360) {
    console.warn(`Hue out of range: ${h}. Clamping to 0-360.`);
  }
  if (s < 0 || s > 1) {
    console.warn(`Saturation out of range: ${s}. Expected 0-1.`);
  }
  if (l < 0 || l > 1) {
    console.warn(`Lightness out of range: ${l}. Expected 0-1.`);
  }

  // Clamp values
  const hClamped = Math.max(0, Math.min(360, h));
  const sClamped = Math.max(0, Math.min(100, sPercent));
  const lClamped = Math.max(0, Math.min(100, lPercent));

  if (a !== undefined) {
    const aClamped = Math.max(0, Math.min(1, a));
    return `hsl(${hClamped}, ${sClamped}%, ${lClamped}%, ${aClamped})`;
  }

  return `hsl(${hClamped}, ${sClamped}%, ${lClamped}%)`;
}

/**
 * Inject CSS variables into the document
 *
 * Updates are batched using requestAnimationFrame for optimal performance.
 * Multiple rapid calls will be combined into a single DOM update.
 *
 * @param updates - Array of variable updates to apply
 * @returns Whether all updates were successful
 *
 * @example
 * injectVariables([
 *   { token: '--background', value: { h: 220, s: 15, l: 18 } },
 *   { token: '--text', value: { h: 220, s: 10, l: 92 } }
 * ]);
 */
export function injectVariables(updates: VariableUpdate[]): boolean {
  if (typeof window === 'undefined') {
    console.warn('CSSVariableInjector: Cannot inject variables in non-browser environment');
    return false;
  }

  try {
    // Add updates to batch
    updates.forEach(({ token, value }) => {
      updateBatch.updates.set(token, value);
    });

    // Cancel existing frame if pending
    if (updateBatch.frameId !== null) {
      cancelAnimationFrame(updateBatch.frameId);
    }

    // Schedule batch update
    updateBatch.frameId = requestAnimationFrame(() => {
      const root = document.documentElement;

      // Apply all batched updates
      updateBatch.updates.forEach((value, token) => {
        const cssValue = hslToCSS(value);
        root.style.setProperty(token, cssValue);
      });

      // Clear batch
      updateBatch.updates.clear();
      updateBatch.frameId = null;
    });

    return true;
  } catch (error) {
    console.error('Failed to inject CSS variables:', error);
    return false;
  }
}

/**
 * Preview CSS variables without committing changes
 *
 * Creates a high-specificity stylesheet that overrides normal styles.
 * Preview changes can be reverted with `revertPreview()`.
 *
 * @param updates - Array of variable updates to preview
 *
 * @example
 * // Preview a color change
 * previewVariables([
 *   { token: '--primary', value: { h: 210, s: 70, l: 50 } }
 * ]);
 *
 * // User decides to cancel
 * revertPreview();
 */
export function previewVariables(updates: VariableUpdate[]): void {
  if (typeof window === 'undefined') return;

  // Create or get preview stylesheet
  if (!previewCache.styleElement) {
    previewCache.styleElement = document.createElement('style');
    previewCache.styleElement.id = 'color-preview-styles';
    previewCache.styleElement.setAttribute('data-preview', 'true');
    document.head.appendChild(previewCache.styleElement);
  }

  // Store original values if not already cached
  const computedStyle = getComputedStyle(document.documentElement);
  updates.forEach(({ token }) => {
    if (!previewCache.originalValues.has(token)) {
      const originalValue = computedStyle.getPropertyValue(token).trim();
      if (originalValue) {
        previewCache.originalValues.set(token, originalValue);
      }
    }
    previewCache.activeTokens.add(token);
  });

  // Build preview CSS with high specificity
  const previewCSS = updates
    .map(({ token, value }) => {
      const cssValue = hslToCSS(value);
      return `--preview${token}: ${cssValue};`;
    })
    .join('\n    ');

  // Apply preview styles
  // Use double :root selector for increased specificity
  previewCache.styleElement.textContent = `
  :root:root {
    ${updates.map(({ token, value }) => `${token}: ${hslToCSS(value)} !important;`).join('\n    ')}
  }

  /* Debug info */
  [data-preview-active]::before {
    content: "Preview Mode Active";
    position: fixed;
    top: 10px;
    right: 10px;
    background: rgba(255, 165, 0, 0.1);
    color: orange;
    padding: 4px 8px;
    border-radius: 4px;
    font-size: 12px;
    z-index: 9999;
    pointer-events: none;
  }
  `;

  // Add preview indicator to body (optional, for debugging)
  document.body.setAttribute('data-preview-active', 'true');
}

/**
 * Revert all preview changes
 *
 * Removes the preview stylesheet and restores original values.
 * Safe to call even if no preview is active.
 *
 * @example
 * // After previewing colors
 * revertPreview(); // Restores original colors
 */
export function revertPreview(): void {
  if (typeof window === 'undefined') return;

  // Remove preview stylesheet
  if (previewCache.styleElement) {
    previewCache.styleElement.remove();
    previewCache.styleElement = null;
  }

  // Clear preview state
  previewCache.originalValues.clear();
  previewCache.activeTokens.clear();

  // Remove preview indicator
  document.body.removeAttribute('data-preview-active');
}

/**
 * Validate that CSS tokens exist in the document
 *
 * Checks if the specified tokens are defined in any stylesheet
 * or inline styles. Useful for preventing errors before injection.
 *
 * @param tokens - Array of CSS variable names to validate
 * @returns Validation result with valid/invalid tokens
 *
 * @example
 * const result = validateTokens(['--background', '--invalid-token']);
 * console.log(result.valid);   // ['--background']
 * console.log(result.invalid); // ['--invalid-token']
 */
export function validateTokens(tokens: string[]): ValidationResult {
  const result: ValidationResult = {
    valid: [],
    invalid: [],
    errors: new Map()
  };

  if (typeof window === 'undefined') {
    result.invalid = tokens;
    result.errors.set('environment', 'Cannot validate tokens in non-browser environment');
    return result;
  }

  const computedStyle = getComputedStyle(document.documentElement);

  tokens.forEach(token => {
    // Check if token starts with --
    if (!token.startsWith('--')) {
      result.invalid.push(token);
      result.errors.set(token, `Invalid token format: must start with '--'`);
      return;
    }

    // Check if token exists in computed styles
    const value = computedStyle.getPropertyValue(token).trim();

    if (value) {
      result.valid.push(token);
    } else {
      // Check stylesheets as fallback
      let found = false;

      try {
        // Check all stylesheets
        for (let i = 0; i < document.styleSheets.length; i++) {
          const stylesheet = document.styleSheets[i];
          try {
            const rules = stylesheet.cssRules || stylesheet.rules;
            for (let j = 0; j < rules.length; j++) {
              const rule = rules[j];
              if (rule instanceof CSSStyleRule) {
                if (rule.style.getPropertyValue(token)) {
                  found = true;
                  break;
                }
              }
            }
            if (found) break;
          } catch (e) {
            // Skip stylesheets we can't access (CORS)
            continue;
          }
        }
      } catch (e) {
        console.warn('Error checking stylesheets:', e);
      }

      if (found) {
        result.valid.push(token);
      } else {
        result.invalid.push(token);
        result.errors.set(token, `Token not found in any stylesheet`);
      }
    }
  });

  return result;
}

/**
 * Get current value of a CSS variable
 *
 * @param token - CSS variable name
 * @returns Current value or null if not found
 *
 * @example
 * const bgColor = getCurrentValue('--background');
 * // Returns: "hsl(220, 15%, 18%)"
 */
export function getCurrentValue(token: string): string | null {
  if (typeof window === 'undefined') return null;

  const computedStyle = getComputedStyle(document.documentElement);
  const value = computedStyle.getPropertyValue(token).trim();

  return value || null;
}

/**
 * Batch inject multiple variables efficiently
 *
 * Optimized version for updating many variables at once.
 * All updates happen in a single animation frame.
 *
 * @param updates - Map of token to HSL color
 * @returns Whether injection was successful
 *
 * @example
 * batchInject(new Map([
 *   ['--background', { h: 220, s: 15, l: 18 }],
 *   ['--surface', { h: 220, s: 15, l: 22 }],
 *   ['--text', { h: 220, s: 10, l: 92 }]
 * ]));
 */
export function batchInject(updates: Map<string, HSLColor>): boolean {
  const updateArray: VariableUpdate[] = Array.from(updates.entries()).map(([token, value]) => ({
    token,
    value
  }));

  return injectVariables(updateArray);
}

/**
 * Clear all injected custom properties
 *
 * Removes all inline style properties from the root element.
 * Use with caution as this affects ALL inline styles.
 */
export function clearInjectedVariables(): void {
  if (typeof window === 'undefined') return;

  const root = document.documentElement;

  // Get all custom properties
  const styles = root.getAttribute('style');
  if (!styles) return;

  // Parse and filter out custom properties
  const nonCustomProps = styles
    .split(';')
    .filter(prop => {
      const trimmed = prop.trim();
      return trimmed && !trimmed.startsWith('--');
    })
    .join(';');

  // Set filtered styles or remove attribute if empty
  if (nonCustomProps) {
    root.setAttribute('style', nonCustomProps);
  } else {
    root.removeAttribute('style');
  }
}

/**
 * Debug utility: Log all current CSS variables
 *
 * @example
 * debugLogVariables();
 * // Logs all CSS custom properties to console
 */
export function debugLogVariables(): void {
  if (typeof window === 'undefined') return;

  const computedStyle = getComputedStyle(document.documentElement);
  const variables: Record<string, string> = {};

  // Get all CSS properties
  for (let i = 0; i < computedStyle.length; i++) {
    const prop = computedStyle[i];
    if (prop.startsWith('--')) {
      variables[prop] = computedStyle.getPropertyValue(prop).trim();
    }
  }

  console.group('CSS Variables');
  console.table(variables);
  console.groupEnd();
}

// Export default object for convenience
export default {
  injectVariables,
  previewVariables,
  revertPreview,
  validateTokens,
  getCurrentValue,
  batchInject,
  clearInjectedVariables,
  hslToCSS,
  debugLogVariables
};