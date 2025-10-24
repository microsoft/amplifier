/**
 * Design Token Utilities
 *
 * CRITICAL: These utilities ensure we NEVER hardcode design values.
 * All design tokens must flow from CSS variables in globals.css.
 *
 * @see .design/ANTI-PATTERNS.md for why this matters
 */

/**
 * Get the computed value of a CSS variable from the document root
 *
 * @param varName - CSS variable name (e.g., '--background')
 * @returns The computed CSS value
 * @throws Error if variable is not defined
 *
 * @example
 * const bgColor = getCSSVariable('--background');  // Returns '#FAFAFF'
 * const spacing = getCSSVariable('--space-4');     // Returns '16px'
 */
export function getCSSVariable(varName: string): string {
  if (typeof window === 'undefined') {
    console.warn(`getCSSVariable('${varName}') called during SSR - returning empty string`);
    return '';
  }

  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(varName)
    .trim();

  if (!value) {
    console.error(`CSS variable '${varName}' is not defined in globals.css!`);
    throw new Error(`Undefined CSS variable: ${varName}`);
  }

  return value;
}

/**
 * Get multiple CSS variables at once
 *
 * @param varNames - Array of CSS variable names
 * @returns Object mapping variable names to their values
 *
 * @example
 * const colors = getCSSVariables(['--background', '--primary', '--text']);
 * // Returns: { '--background': '#FAFAFF', '--primary': '#8A8DD0', '--text': '#1C1C1C' }
 */
export function getCSSVariables(varNames: string[]): Record<string, string> {
  const result: Record<string, string> = {};

  for (const varName of varNames) {
    result[varName] = getCSSVariable(varName);
  }

  return result;
}

/**
 * Check if a CSS variable is defined
 *
 * @param varName - CSS variable name
 * @returns true if defined, false otherwise
 *
 * @example
 * if (hasCSSVariable('--background')) {
 *   // Safe to use
 * }
 */
export function hasCSSVariable(varName: string): boolean {
  if (typeof window === 'undefined') return false;

  const value = getComputedStyle(document.documentElement)
    .getPropertyValue(varName)
    .trim();

  return value.length > 0;
}

/**
 * Development-only validation
 * Logs a warning if a value doesn't match its CSS variable
 *
 * @param varName - CSS variable name
 * @param value - The value to validate
 *
 * @example
 * validateCSSVariable('--background', '#FAFAFF');  // OK if they match
 * validateCSSVariable('--background', '#000000');   // Warns if mismatch
 */
export function validateCSSVariable(varName: string, value: string): void {
  if (process.env.NODE_ENV !== 'development') return;
  if (typeof window === 'undefined') return;

  try {
    const cssValue = getCSSVariable(varName);

    // Normalize for comparison (remove whitespace, make lowercase)
    const normalizedCSS = cssValue.replace(/\s/g, '').toLowerCase();
    const normalizedValue = value.replace(/\s/g, '').toLowerCase();

    if (normalizedCSS !== normalizedValue) {
      console.warn('⚠️  CSS Variable Mismatch Detected');
      console.warn(`  Variable: ${varName}`);
      console.warn(`  CSS Value: ${cssValue}`);
      console.warn(`  Code Value: ${value}`);
      console.warn(`  This is likely a bug - values should match!`);
    }
  } catch (error) {
    console.error(`Failed to validate ${varName}:`, error);
  }
}