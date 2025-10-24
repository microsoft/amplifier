/**
 * Color parsing utilities for converting between CSS color formats and HSL
 */

import type { HSLColor } from '../../packages/color-intelligence/types';

/**
 * Parse CSS HSL string to HSLColor object
 * Converts percentage values to decimal (0-1)
 * Example: hsl(220, 15%, 12%) -> { h: 220, s: 0.15, l: 0.12 }
 */
export function parseCSSHSL(cssValue: string): HSLColor | null {
  const match = cssValue.match(/hsl\((\d+),?\s*(\d+)%,?\s*(\d+)%(?:,?\s*([\d.]+))?\)/);
  if (!match) return null;

  return {
    h: parseInt(match[1], 10),
    s: parseInt(match[2], 10) / 100,  // Convert percentage to decimal
    l: parseInt(match[3], 10) / 100,  // Convert percentage to decimal
    ...(match[4] && { a: parseFloat(match[4]) })
  };
}

/**
 * Parse CSS hex color to HSLColor object
 * Example: #FAFAFF -> { h: 240, s: 1, l: 0.99 }
 */
export function hexToHSL(hex: string): HSLColor | null {
  // Remove # if present
  hex = hex.replace(/^#/, '');

  // Parse hex values
  let r: number, g: number, b: number;

  if (hex.length === 3) {
    // Short form (e.g., #FFF)
    r = parseInt(hex[0] + hex[0], 16) / 255;
    g = parseInt(hex[1] + hex[1], 16) / 255;
    b = parseInt(hex[2] + hex[2], 16) / 255;
  } else if (hex.length === 6) {
    // Full form (e.g., #FAFAFF)
    r = parseInt(hex.substring(0, 2), 16) / 255;
    g = parseInt(hex.substring(2, 4), 16) / 255;
    b = parseInt(hex.substring(4, 6), 16) / 255;
  } else {
    return null;
  }

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const diff = max - min;

  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (diff !== 0) {
    s = l > 0.5 ? diff / (2 - max - min) : diff / (max + min);

    switch (max) {
      case r:
        h = ((g - b) / diff + (g < b ? 6 : 0)) * 60;
        break;
      case g:
        h = ((b - r) / diff + 2) * 60;
        break;
      case b:
        h = ((r - g) / diff + 4) * 60;
        break;
    }
  }

  return {
    h: Math.round(h),
    s: Math.round(s * 100) / 100,  // Keep as decimal (0-1)
    l: Math.round(l * 100) / 100   // Keep as decimal (0-1)
  };
}

/**
 * Parse CSS RGB/RGBA string to HSLColor object
 * Example: rgb(250, 250, 255) -> { h: 240, s: 1, l: 0.99 }
 */
export function rgbToHSL(rgb: string): HSLColor | null {
  const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*([\d.]+))?\)/);
  if (!match) return null;

  const r = parseInt(match[1], 10) / 255;
  const g = parseInt(match[2], 10) / 255;
  const b = parseInt(match[3], 10) / 255;
  const a = match[4] ? parseFloat(match[4]) : undefined;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const diff = max - min;

  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (diff !== 0) {
    s = l > 0.5 ? diff / (2 - max - min) : diff / (max + min);

    switch (max) {
      case r:
        h = ((g - b) / diff + (g < b ? 6 : 0)) * 60;
        break;
      case g:
        h = ((b - r) / diff + 2) * 60;
        break;
      case b:
        h = ((r - g) / diff + 4) * 60;
        break;
    }
  }

  return {
    h: Math.round(h),
    s: Math.round(s * 100) / 100,  // Keep as decimal (0-1)
    l: Math.round(l * 100) / 100,  // Keep as decimal (0-1)
    ...(a !== undefined && { a })
  };
}

/**
 * Parse any CSS color value to HSLColor
 * Supports: hsl(), hex (#FFF, #FFFFFF), rgb(), rgba()
 */
export function parseCSSColor(cssValue: string): HSLColor | null {
  cssValue = cssValue.trim();

  // Try HSL first
  if (cssValue.startsWith('hsl')) {
    return parseCSSHSL(cssValue);
  }

  // Try hex
  if (cssValue.startsWith('#')) {
    return hexToHSL(cssValue);
  }

  // Try RGB/RGBA
  if (cssValue.startsWith('rgb')) {
    return rgbToHSL(cssValue);
  }

  // Named colors or invalid format
  return null;
}

/**
 * Resolve a CSS variable to its computed value
 * Handles nested var() references
 */
export function resolveCSSVariable(varName: string): string {
  if (typeof window === 'undefined') return '';

  const computed = getComputedStyle(document.documentElement);
  let value = computed.getPropertyValue(varName).trim();

  // Resolve nested var() references
  while (value.includes('var(')) {
    const varMatch = value.match(/var\((--[^)]+)\)/);
    if (!varMatch) break;

    const nestedVar = varMatch[1];
    const nestedValue = computed.getPropertyValue(nestedVar).trim();
    if (!nestedValue) break;

    value = value.replace(varMatch[0], nestedValue);
  }

  return value;
}