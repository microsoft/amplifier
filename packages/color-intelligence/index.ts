/**
 * Color Intelligence Module
 *
 * A self-contained module for analyzing color changes using color theory principles.
 * Provides comprehensive analysis of harmony, contrast, semantics, and perception.
 * Includes intelligent suggestion generation for palette adjustments.
 *
 * @module @amplified/color-intelligence
 */

// Main analyzer function (with alias for compatibility)
export { analyzeColor, analyzeColor as analyzeColorChange } from './analyzer';

// Main suggestion engine function
export { generateSuggestions } from './suggestions';

// Core analysis functions
export {
  calculateHarmony,
  validateContrast,
  assessSemantics,
  predictPerception,
} from './analyzer';

// Utility functions
export {
  hslToRgb,
  rgbToHsl,
  relativeLuminance,
  contrastRatio,
  hueAngle,
  normalizeHue,
  colorTemperature,
  blendColors,
  perceivedBrightness,
  calculateVibrancy,
  calculateRefinement,
  isHueInRange,
  visualWeight,
  areSimilar,
} from './utils';

// Constants
export {
  WCAG_REQUIREMENTS,
  SEMANTIC_HUE_RANGES,
  SEMANTIC_SATURATION_RANGES,
  SEMANTIC_LIGHTNESS_RANGES,
  HARMONY_ANGLES,
  SWEDISH_AESTHETIC,
  PERCEPTION_FACTORS,
  QUALITY_WEIGHTS,
  TEMPERATURE_RANGES,
  LUMINANCE_WEIGHTS,
  GAMMA,
  PERFORMANCE,
} from './constants';

// Types
export type {
  // Core types
  HSLColor,
  ColorPalette,
  UsageContext,
  HueRange,
  ColorRelationship,

  // Analysis types
  HarmonyAnalysis,
  ContrastAnalysis,
  SemanticAnalysis,
  PerceptionAnalysis,
  QualityMetrics,
  ColorAnalysis,

  // Impact types
  ImpactSeverity,
  ImpactReport,

  // Main I/O types
  AnalyzerInput,
  AnalyzerOutput,

  // Color theory types
  ContrastType,
  IttenContrast,

  // Suggestion engine types
  DesignIntent,
  QualityConstraints,
  ColorChange,
  QualityScore,
  ColorSuggestion,
  HarmonyType,
  SuggestionEngineInput,
  SuggestionEngineOutput,
} from './types';