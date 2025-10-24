/**
 * Color Utility Functions
 *
 * Core utilities for color space conversions, calculations, and manipulations.
 * All calculations are optimized for performance (<5ms total).
 */

import type { HSLColor } from './types';
import { LUMINANCE_WEIGHTS, GAMMA } from './constants';

/**
 * Convert HSL to RGB
 * @param hsl HSL color object
 * @returns RGB values [0-255, 0-255, 0-255]
 */
export function hslToRgb(hsl: HSLColor): [number, number, number] {
  const h = hsl.h / 360;
  const s = hsl.s / 100;
  const l = hsl.l / 100;

  let r: number, g: number, b: number;

  if (s === 0) {
    // Achromatic
    r = g = b = l;
  } else {
    const hue2rgb = (p: number, q: number, t: number): number => {
      if (t < 0) t += 1;
      if (t > 1) t -= 1;
      if (t < 1/6) return p + (q - p) * 6 * t;
      if (t < 1/2) return q;
      if (t < 2/3) return p + (q - p) * (2/3 - t) * 6;
      return p;
    };

    const q = l < 0.5 ? l * (1 + s) : l + s - l * s;
    const p = 2 * l - q;

    r = hue2rgb(p, q, h + 1/3);
    g = hue2rgb(p, q, h);
    b = hue2rgb(p, q, h - 1/3);
  }

  return [
    Math.round(r * 255),
    Math.round(g * 255),
    Math.round(b * 255),
  ];
}

/**
 * Convert RGB to HSL
 * @param r Red value [0-255]
 * @param g Green value [0-255]
 * @param b Blue value [0-255]
 * @returns HSL color object
 */
export function rgbToHsl(r: number, g: number, b: number): HSLColor {
  r /= 255;
  g /= 255;
  b /= 255;

  const max = Math.max(r, g, b);
  const min = Math.min(r, g, b);
  let h = 0;
  let s = 0;
  const l = (max + min) / 2;

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
    h: Math.round(h * 360),
    s: Math.round(s * 100),
    l: Math.round(l * 100),
  };
}

/**
 * Calculate relative luminance for WCAG contrast
 * @param rgb RGB values [0-255, 0-255, 0-255]
 * @returns Relative luminance [0-1]
 */
export function relativeLuminance(rgb: [number, number, number]): number {
  const [r, g, b] = rgb.map(val => {
    const srgb = val / 255;
    return srgb <= 0.03928
      ? srgb / 12.92
      : Math.pow((srgb + 0.055) / 1.055, GAMMA);
  });

  return (
    LUMINANCE_WEIGHTS.RED * r +
    LUMINANCE_WEIGHTS.GREEN * g +
    LUMINANCE_WEIGHTS.BLUE * b
  );
}

/**
 * Calculate WCAG contrast ratio between two colors
 * @param color1 First HSL color
 * @param color2 Second HSL color
 * @returns Contrast ratio (1-21)
 */
export function contrastRatio(color1: HSLColor, color2: HSLColor): number {
  const rgb1 = hslToRgb(color1);
  const rgb2 = hslToRgb(color2);

  const lum1 = relativeLuminance(rgb1);
  const lum2 = relativeLuminance(rgb2);

  const lighter = Math.max(lum1, lum2);
  const darker = Math.min(lum1, lum2);

  return (lighter + 0.05) / (darker + 0.05);
}

/**
 * Calculate angle between two hues on the color wheel
 * @param hue1 First hue [0-360]
 * @param hue2 Second hue [0-360]
 * @returns Shortest angle between hues [0-180]
 */
export function hueAngle(hue1: number, hue2: number): number {
  let angle = Math.abs(hue1 - hue2);
  if (angle > 180) {
    angle = 360 - angle;
  }
  return angle;
}

/**
 * Normalize hue to 0-360 range
 * @param hue Any hue value
 * @returns Normalized hue [0-360]
 */
export function normalizeHue(hue: number): number {
  hue = hue % 360;
  return hue < 0 ? hue + 360 : hue;
}

/**
 * Calculate color temperature (warm vs cool)
 * @param hue Hue value [0-360]
 * @returns Temperature value [-1 to 1], negative = cool, positive = warm
 */
export function colorTemperature(hue: number): number {
  hue = normalizeHue(hue);

  // Warmest at 30° (orange), coolest at 210° (blue)
  const warmCenter = 30;
  const coolCenter = 210;

  const warmDistance = hueAngle(hue, warmCenter);
  const coolDistance = hueAngle(hue, coolCenter);

  // Normalize to -1 to 1 scale
  if (warmDistance < coolDistance) {
    return 1 - (warmDistance / 90); // Max warm distance is 90°
  } else {
    return -(1 - (coolDistance / 90)); // Max cool distance is 90°
  }
}

/**
 * Blend two colors (simple average in HSL)
 * @param color1 First color
 * @param color2 Second color
 * @param weight Weight of first color [0-1]
 * @returns Blended color
 */
export function blendColors(color1: HSLColor, color2: HSLColor, weight: number = 0.5): HSLColor {
  // Handle hue wrapping for shortest path
  let h1 = color1.h;
  let h2 = color2.h;

  if (Math.abs(h1 - h2) > 180) {
    if (h1 > h2) {
      h2 += 360;
    } else {
      h1 += 360;
    }
  }

  return {
    h: normalizeHue(h1 * weight + h2 * (1 - weight)),
    s: color1.s * weight + color2.s * (1 - weight),
    l: color1.l * weight + color2.l * (1 - weight),
    a: color1.a !== undefined && color2.a !== undefined
      ? color1.a * weight + color2.a * (1 - weight)
      : undefined,
  };
}

/**
 * Calculate perceived brightness (different from lightness)
 * Accounts for human perception differences across hues
 * @param color HSL color
 * @returns Perceived brightness [0-100]
 */
export function perceivedBrightness(color: HSLColor): number {
  const [r, g, b] = hslToRgb(color);
  // Using simplified perceived brightness formula
  return Math.sqrt(
    0.299 * r * r +
    0.587 * g * g +
    0.114 * b * b
  ) / 255 * 100;
}

/**
 * Calculate color vibrancy/intensity
 * @param color HSL color
 * @returns Vibrancy score [0-10]
 */
export function calculateVibrancy(color: HSLColor): number {
  // Vibrancy is highest with high saturation and medium lightness
  const saturationScore = color.s / 100;
  const lightnessScore = 1 - Math.abs(color.l - 50) / 50; // Peak at L=50

  return saturationScore * lightnessScore * 10;
}

/**
 * Calculate color refinement (subtlety)
 * Swedish aesthetic prefers refined, subtle colors
 * @param color HSL color
 * @returns Refinement score [0-10]
 */
export function calculateRefinement(color: HSLColor): number {
  // Lower saturation and mid-range lightness = more refined
  const saturationRefinement = 1 - (color.s / 100) * 0.7; // Lower sat = higher refinement
  const lightnessRefinement = 1 - Math.abs(color.l - 60) / 40; // Peak around L=60

  // Certain hues are considered more refined
  const hueRefinement = getHueRefinement(color.h);

  return (saturationRefinement * 0.4 + lightnessRefinement * 0.3 + hueRefinement * 0.3) * 10;
}

/**
 * Get refinement score for specific hue
 * @param hue Hue value [0-360]
 * @returns Hue refinement score [0-1]
 */
function getHueRefinement(hue: number): number {
  hue = normalizeHue(hue);

  // Blues, grays, and muted greens are most refined
  // Bright reds and yellows are least refined
  if (hue >= 200 && hue <= 250) return 0.9; // Blues
  if (hue >= 150 && hue <= 170) return 0.8; // Blue-greens
  if (hue >= 90 && hue <= 120) return 0.7;  // Greens
  if (hue >= 20 && hue <= 40) return 0.5;   // Oranges
  if (hue >= 50 && hue <= 70) return 0.4;   // Yellows
  if (hue >= 0 && hue <= 10) return 0.3;    // Reds
  if (hue >= 350 && hue <= 360) return 0.3; // Reds (wrapped)

  return 0.6; // Default
}

/**
 * Check if color is within a hue range
 * Handles wrapping around 0/360
 * @param hue Hue to check
 * @param min Minimum hue
 * @param max Maximum hue
 * @returns Whether hue is in range
 */
export function isHueInRange(hue: number, min: number, max: number): boolean {
  hue = normalizeHue(hue);
  min = normalizeHue(min);
  max = normalizeHue(max);

  if (min <= max) {
    return hue >= min && hue <= max;
  } else {
    // Range wraps around 0/360
    return hue >= min || hue <= max;
  }
}

/**
 * Calculate the visual weight of a color
 * Darker and more saturated colors have more weight
 * @param color HSL color
 * @returns Visual weight [0-10]
 */
export function visualWeight(color: HSLColor): number {
  const darkness = 1 - (color.l / 100);
  const saturation = color.s / 100;

  return (darkness * 0.7 + saturation * 0.3) * 10;
}

/**
 * Check if two colors are perceptually similar
 * @param color1 First color
 * @param color2 Second color
 * @param threshold Similarity threshold
 * @returns Whether colors are similar
 */
export function areSimilar(color1: HSLColor, color2: HSLColor, threshold: number = 10): boolean {
  const hueDiff = hueAngle(color1.h, color2.h);
  const satDiff = Math.abs(color1.s - color2.s);
  const lightDiff = Math.abs(color1.l - color2.l);

  // Weighted difference (hue matters less at low saturation)
  const satWeight = Math.min(color1.s, color2.s) / 100;
  const totalDiff = (hueDiff * satWeight) + (satDiff * 0.5) + (lightDiff * 1.5);

  return totalDiff < threshold;
}