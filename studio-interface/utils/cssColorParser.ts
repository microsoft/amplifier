/**
 * CSS Color Parser - Parse CSS color values to HSL
 * Handles rgb(), hsl(), hex, and named colors
 */

import { HSLColor } from '@/packages/color-intelligence/types';

/**
 * Parse any CSS color string to HSL
 */
export function parseCSSColor(cssColor: string): HSLColor | null {
  if (!cssColor) return null;

  const color = cssColor.trim().toLowerCase();

  // Try parsing different formats
  if (color.startsWith('#')) {
    return hexToHSL(color);
  } else if (color.startsWith('rgb')) {
    return rgbStringToHSL(color);
  } else if (color.startsWith('hsl')) {
    return hslStringToHSL(color);
  } else if (namedColors[color]) {
    return hexToHSL(namedColors[color]);
  }

  // Try to parse from computed style
  return parseFromComputed(color);
}

/**
 * Convert hex color to HSL
 */
function hexToHSL(hex: string): HSLColor | null {
  const result = /^#?([a-f\d]{2})([a-f\d]{2})([a-f\d]{2})$/i.exec(hex);
  if (!result) return null;

  const r = parseInt(result[1], 16) / 255;
  const g = parseInt(result[2], 16) / 255;
  const b = parseInt(result[3], 16) / 255;

  return rgbToHSL(r, g, b);
}

/**
 * Parse RGB string to HSL
 */
function rgbStringToHSL(rgb: string): HSLColor | null {
  const match = rgb.match(/rgba?\((\d+),\s*(\d+),\s*(\d+)/);
  if (!match) return null;

  const r = parseInt(match[1]) / 255;
  const g = parseInt(match[2]) / 255;
  const b = parseInt(match[3]) / 255;

  return rgbToHSL(r, g, b);
}

/**
 * Parse HSL string to HSL object
 */
function hslStringToHSL(hsl: string): HSLColor | null {
  const match = hsl.match(/hsla?\((\d+),\s*(\d+)%,\s*(\d+)%/);
  if (!match) return null;

  return {
    hue: parseInt(match[1]),
    saturation: parseInt(match[2]),
    lightness: parseInt(match[3])
  };
}

/**
 * Convert RGB to HSL
 */
function rgbToHSL(r: number, g: number, b: number): HSLColor {
  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0, s = 0, l = (max + min) / 2;

  if (max !== min) {
    const d = max - min;
    s = l > 0.5 ? d / (2 - max - min) : d / (max + min);

    switch (max) {
      case r:
        h = ((g - b) / d + (g < b ? 6 : 0)) / 6;
        break;
      case g:
        h = ((b - r) / d + 2) / 6;
        break;
      case b:
        h = ((r - g) / d + 4) / 6;
        break;
    }
  }

  return {
    hue: Math.round(h * 360),
    saturation: Math.round(s * 100),
    lightness: Math.round(l * 100)
  };
}

/**
 * Convert HSL to CSS string
 */
export function hslToCSS(hsl: HSLColor): string {
  return `hsl(${hsl.hue}, ${hsl.saturation}%, ${hsl.lightness}%)`;
}

/**
 * Convert HSL to hex
 */
export function hslToHex(hsl: HSLColor): string {
  const { hue, saturation, lightness } = hsl;
  const l = lightness / 100;
  const s = saturation / 100;

  const c = (1 - Math.abs(2 * l - 1)) * s;
  const x = c * (1 - Math.abs((hue / 60) % 2 - 1));
  const m = l - c / 2;

  let r = 0, g = 0, b = 0;

  if (hue >= 0 && hue < 60) {
    r = c; g = x; b = 0;
  } else if (hue >= 60 && hue < 120) {
    r = x; g = c; b = 0;
  } else if (hue >= 120 && hue < 180) {
    r = 0; g = c; b = x;
  } else if (hue >= 180 && hue < 240) {
    r = 0; g = x; b = c;
  } else if (hue >= 240 && hue < 300) {
    r = x; g = 0; b = c;
  } else if (hue >= 300 && hue < 360) {
    r = c; g = 0; b = x;
  }

  const toHex = (n: number) => {
    const hex = Math.round((n + m) * 255).toString(16);
    return hex.length === 1 ? '0' + hex : hex;
  };

  return `#${toHex(r)}${toHex(g)}${toHex(b)}`;
}

/**
 * Parse from computed style (fallback)
 */
function parseFromComputed(value: string): HSLColor | null {
  if (typeof window === 'undefined') return null;

  try {
    const div = document.createElement('div');
    div.style.color = value;
    document.body.appendChild(div);
    const computed = window.getComputedStyle(div).color;
    document.body.removeChild(div);

    if (computed && computed !== value) {
      return rgbStringToHSL(computed);
    }
  } catch (e) {
    console.error('Failed to parse computed color:', e);
  }

  return null;
}

/**
 * Load all CSS color variables
 */
export function loadColorsFromCSS(): Record<string, HSLColor> {
  if (typeof window === 'undefined') return {};

  const colors: Record<string, HSLColor> = {};
  const computedStyle = getComputedStyle(document.documentElement);

  // Color tokens to load
  const colorTokens = [
    // Core palette
    'color-primary',
    'color-secondary',
    'color-accent',
    'color-surface',
    'color-background',
    'color-foreground',

    // Semantic colors
    'color-success',
    'color-warning',
    'color-error',
    'color-info',

    // UI colors
    'color-border',
    'color-border-subtle',
    'color-text',
    'color-text-secondary',
    'color-text-tertiary',

    // Interactive states
    'color-hover',
    'color-active',
    'color-focus',
    'color-disabled'
  ];

  for (const token of colorTokens) {
    const cssValue = computedStyle.getPropertyValue(`--${token}`).trim();
    if (cssValue) {
      const hsl = parseCSSColor(cssValue);
      if (hsl) {
        colors[token] = hsl;
      }
    }
  }

  return colors;
}

/**
 * Inject CSS variable
 */
export function injectCSSVariable(token: string, color: HSLColor): void {
  if (typeof window === 'undefined') return;

  const cssValue = hslToCSS(color);
  document.documentElement.style.setProperty(`--${token}`, cssValue);
}

/**
 * Common named colors
 */
const namedColors: Record<string, string> = {
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
  'silver': '#c0c0c0',
  'maroon': '#800000',
  'olive': '#808000',
  'lime': '#00ff00',
  'aqua': '#00ffff',
  'teal': '#008080',
  'navy': '#000080',
  'fuchsia': '#ff00ff',
  'purple': '#800080'
};