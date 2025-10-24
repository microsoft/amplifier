/**
 * Color conversion utilities for CSS variable injection
 * Handles HSL, RGB, and Hex color format conversions
 */

import { HSLColor } from '../types/color';

/**
 * Convert HSL object to CSS string format
 */
export function hslToCSSString(hsl: HSLColor): string {
  const h = Math.round(hsl.h);
  const s = Math.round(hsl.s);
  const l = Math.round(hsl.l);
  return `hsl(${h}, ${s}%, ${l}%)`;
}

/**
 * Parse HSL string to object
 * Handles formats: hsl(240, 100%, 50%) and hsl(240deg, 100%, 50%)
 */
export function parseHSLString(hsl: string): HSLColor | null {
  const match = hsl.match(/hsl\((\d+)(?:deg)?,\s*(\d+)%,\s*(\d+)%\)/);
  if (!match) return null;

  return {
    h: parseInt(match[1]),
    s: parseInt(match[2]),
    l: parseInt(match[3]),
  };
}

/**
 * Convert hex color to RGB
 */
export function hexToRGB(hex: string): { r: number; g: number; b: number } {
  // Remove # if present
  const cleanHex = hex.replace('#', '');

  // Handle 3-digit hex
  const fullHex = cleanHex.length === 3
    ? cleanHex.split('').map(char => char + char).join('')
    : cleanHex;

  const bigint = parseInt(fullHex, 16);
  return {
    r: (bigint >> 16) & 255,
    g: (bigint >> 8) & 255,
    b: bigint & 255,
  };
}

/**
 * Convert RGB to HSL
 * Based on standard RGB to HSL conversion algorithm
 */
export function rgbToHSL(rgb: string | { r: number; g: number; b: number }): HSLColor {
  let r: number, g: number, b: number;

  if (typeof rgb === 'string') {
    // Parse rgb(r, g, b) or rgba(r, g, b, a) string
    const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)(?:,\s*[\d.]+)?\)/);
    if (!match) {
      return { h: 0, s: 0, l: 0 };
    }
    r = parseInt(match[1]);
    g = parseInt(match[2]);
    b = parseInt(match[3]);
  } else {
    r = rgb.r;
    g = rgb.g;
    b = rgb.b;
  }

  // Normalize RGB values to 0-1
  r /= 255;
  g /= 255;
  b /= 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  const diff = max - min;

  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

  if (diff !== 0) {
    // Calculate saturation
    s = l > 0.5
      ? diff / (2 - max - min)
      : diff / (max + min);

    // Calculate hue
    switch (max) {
      case r:
        h = ((g - b) / diff + (g < b ? 6 : 0)) / 6;
        break;
      case g:
        h = ((b - r) / diff + 2) / 6;
        break;
      case b:
        h = ((r - g) / diff + 4) / 6;
        break;
    }
  }

  return {
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100),
  };
}

/**
 * Convert hex color to HSL
 */
export function hexToHSL(hex: string): HSLColor {
  const rgb = hexToRGB(hex);
  return rgbToHSL(rgb);
}

/**
 * Interpolate between two HSL colors
 * @param from - Starting color
 * @param to - Target color
 * @param progress - Progress value between 0 and 1
 */
export function interpolateHSL(from: HSLColor, to: HSLColor, progress: number): HSLColor {
  // Clamp progress between 0 and 1
  const p = Math.max(0, Math.min(1, progress));

  // Handle hue interpolation (shortest path on color wheel)
  let h1 = from.h;
  let h2 = to.h;
  const hDiff = h2 - h1;

  // Choose shortest path around the color wheel
  if (hDiff > 180) {
    h2 -= 360;
  } else if (hDiff < -180) {
    h2 += 360;
  }

  const h = lerp(h1, h2, p);

  return {
    h: ((h % 360) + 360) % 360, // Normalize to 0-360
    s: lerp(from.s, to.s, p),
    l: lerp(from.l, to.l, p),
  };
}

/**
 * Linear interpolation between two numbers
 */
export function lerp(start: number, end: number, progress: number): number {
  return start + (end - start) * progress;
}

/**
 * Check if a CSS color value is valid
 * Supports: hsl(), rgb(), rgba(), hex colors
 */
export function isValidCSSColor(value: string): boolean {
  if (!value || value.trim() === '') return false;

  const trimmed = value.trim();

  // Check for HSL
  if (trimmed.startsWith('hsl')) {
    return /^hsl\(\d+(?:deg)?,\s*\d+%,\s*\d+%\)$/.test(trimmed);
  }

  // Check for RGB/RGBA
  if (trimmed.startsWith('rgb')) {
    return /^rgba?\(\d+,\s*\d+,\s*\d+(?:,\s*[\d.]+)?\)$/.test(trimmed);
  }

  // Check for hex
  if (trimmed.startsWith('#')) {
    return /^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$/.test(trimmed);
  }

  // Check for named colors (basic set)
  const namedColors = [
    'transparent', 'white', 'black', 'red', 'green', 'blue',
    'yellow', 'cyan', 'magenta', 'gray', 'grey'
  ];
  return namedColors.includes(trimmed.toLowerCase());
}

/**
 * Parse any CSS color format to HSL
 */
export function parseCSSColor(cssValue: string): HSLColor | null {
  if (!cssValue || cssValue.trim() === '') return null;

  const trimmed = cssValue.trim();

  // Handle HSL
  if (trimmed.startsWith('hsl')) {
    return parseHSLString(trimmed);
  }

  // Handle hex
  if (trimmed.startsWith('#')) {
    return hexToHSL(trimmed);
  }

  // Handle RGB/RGBA
  if (trimmed.startsWith('rgb')) {
    return rgbToHSL(trimmed);
  }

  // Handle named colors (basic set)
  const namedColorMap: Record<string, string> = {
    'white': '#ffffff',
    'black': '#000000',
    'red': '#ff0000',
    'green': '#008000',
    'blue': '#0000ff',
    'yellow': '#ffff00',
    'cyan': '#00ffff',
    'magenta': '#ff00ff',
    'gray': '#808080',
    'grey': '#808080',
    'transparent': '#00000000',
  };

  const lowerCased = trimmed.toLowerCase();
  if (lowerCased in namedColorMap) {
    return hexToHSL(namedColorMap[lowerCased]);
  }

  return null;
}