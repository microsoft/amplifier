/**
 * Color Theory Constants
 *
 * Fundamental constants and thresholds based on color theory principles
 * and accessibility standards.
 */

import type { HueRange } from './types';

/**
 * WCAG Contrast Requirements
 */
export const WCAG_REQUIREMENTS = {
  /** Large text (18pt+ or 14pt+ bold) */
  LARGE_TEXT: {
    AA: 3.0,
    AAA: 4.5,
  },
  /** Normal text */
  NORMAL_TEXT: {
    AA: 4.5,
    AAA: 7.0,
  },
  /** UI components and graphical objects */
  UI_COMPONENTS: {
    AA: 3.0,
    AAA: 4.5,
  },
} as const;

/**
 * Semantic color hue ranges
 * Based on cultural color associations and best practices
 */
export const SEMANTIC_HUE_RANGES: Record<string, HueRange> = {
  success: {
    min: 100,
    max: 140,
    ideal: 120, // Pure green
  },
  warning: {
    min: 30,
    max: 50,
    ideal: 40, // Orange-yellow
  },
  error: {
    min: 350,
    max: 10,
    ideal: 0, // Pure red (wraps around 360)
  },
  info: {
    min: 200,
    max: 230,
    ideal: 210, // Sky blue
  },
  primary: {
    min: 210,
    max: 250,
    ideal: 230, // Professional blue
  },
} as const;

/**
 * Semantic saturation ranges
 * For appropriate intensity based on role
 */
export const SEMANTIC_SATURATION_RANGES: Record<string, { min: number; max: number; ideal: number }> = {
  success: { min: 60, max: 70, ideal: 65 },
  warning: { min: 80, max: 90, ideal: 85 },
  error: { min: 65, max: 75, ideal: 70 },
  info: { min: 60, max: 70, ideal: 65 },
  primary: { min: 70, max: 85, ideal: 75 },
} as const;

/**
 * Semantic lightness ranges
 * For optimal visibility and hierarchy
 */
export const SEMANTIC_LIGHTNESS_RANGES: Record<string, { min: number; max: number; ideal: number }> = {
  success: { min: 45, max: 55, ideal: 50 },
  warning: { min: 50, max: 60, ideal: 55 },
  error: { min: 50, max: 60, ideal: 55 },
  info: { min: 50, max: 60, ideal: 55 },
  primary: { min: 45, max: 55, ideal: 50 },
} as const;

/**
 * Color harmony angle tolerances (in degrees)
 */
export const HARMONY_ANGLES = {
  COMPLEMENTARY: {
    angle: 180,
    tolerance: 15,
  },
  ANALOGOUS: {
    angle: 30,
    tolerance: 15,
  },
  TRIADIC: {
    angle: 120,
    tolerance: 15,
  },
  SPLIT_COMPLEMENTARY: {
    angle: 150,
    tolerance: 15,
  },
  TETRADIC: {
    angle: 90,
    tolerance: 15,
  },
  MONOCHROMATIC: {
    angle: 0,
    tolerance: 10,
  },
} as const;

/**
 * Swedish design aesthetic preferences
 * Emphasizing subtlety and refinement
 */
export const SWEDISH_AESTHETIC = {
  /** Preferred saturation for refined look */
  SATURATION: {
    min: 15,
    max: 70,
    ideal: 40,
  },
  /** Preferred lightness for balanced contrast */
  LIGHTNESS: {
    min: 20,
    max: 90,
    ideal: 60,
  },
  /** Maximum hue variance for cohesive palettes */
  HUE_VARIANCE: {
    tight: 30,  // Very cohesive
    medium: 60, // Balanced
    loose: 120, // More variety
  },
  /** Quality thresholds */
  QUALITY: {
    minimum: 8.5,
    target: 9.5,
  },
} as const;

/**
 * Perceptual shift factors
 * How much context affects color appearance
 */
export const PERCEPTION_FACTORS = {
  /** Maximum hue shift from context (degrees) */
  MAX_HUE_SHIFT: 15,
  /** Maximum saturation shift (percentage) */
  MAX_SATURATION_SHIFT: 20,
  /** Maximum lightness shift (percentage) */
  MAX_LIGHTNESS_SHIFT: 15,
  /** Influence weights for adjacent colors */
  ADJACENT_INFLUENCE: {
    immediate: 0.4,  // Directly touching
    near: 0.2,       // Close proximity
    distant: 0.1,    // Same view
  },
} as const;

/**
 * Quality scoring weights
 * For calculating overall quality metrics
 */
export const QUALITY_WEIGHTS = {
  HARMONY: 0.25,
  CONTRAST: 0.25,
  SEMANTICS: 0.20,
  REFINEMENT: 0.15,
  BALANCE: 0.15,
} as const;

/**
 * Temperature boundaries (in hue degrees)
 * For warm/cool color classification
 */
export const TEMPERATURE_RANGES = {
  WARM: {
    start: 0,    // Red
    end: 60,     // Yellow
    peak: 30,    // Orange
  },
  COOL: {
    start: 180,  // Cyan
    end: 300,    // Magenta
    peak: 240,   // Blue
  },
  NEUTRAL: {
    warmEdge: [60, 90],   // Yellow-green
    coolEdge: [150, 180], // Green-cyan
  },
} as const;

/**
 * Relative luminance RGB weights
 * For WCAG contrast calculations
 */
export const LUMINANCE_WEIGHTS = {
  RED: 0.2126,
  GREEN: 0.7152,
  BLUE: 0.0722,
} as const;

/**
 * Gamma correction for sRGB
 */
export const GAMMA = 2.4 as const;

/**
 * Performance thresholds
 */
export const PERFORMANCE = {
  /** Maximum time for full analysis (ms) */
  MAX_ANALYSIS_TIME: 5,
  /** Cache TTL for calculations (ms) */
  CACHE_TTL: 1000,
} as const;