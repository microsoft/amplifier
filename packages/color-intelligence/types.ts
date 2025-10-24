/**
 * Color Intelligence Type Definitions
 *
 * Core type system for color analysis and intelligence.
 * All color calculations use HSL as the primary color space.
 */

/**
 * HSL color representation
 * The foundation of all color calculations
 */
export interface HSLColor {
  /** Hue: 0-360 degrees on the color wheel */
  h: number;
  /** Saturation: 0-100 percentage */
  s: number;
  /** Lightness: 0-100 percentage */
  l: number;
  /** Alpha/opacity: 0-1 (optional) */
  a?: number;
}

/**
 * Complete color palette for a design system
 */
export interface ColorPalette {
  background: HSLColor;
  surface: HSLColor;
  text: HSLColor;
  textMuted: HSLColor;
  border: HSLColor;
  primary: HSLColor;
  accent: HSLColor;
  success: HSLColor;
  warning: HSLColor;
  error: HSLColor;
  info: HSLColor;
}

/**
 * Context in which a color is being used
 */
export interface UsageContext {
  /** The semantic role of this color */
  role: 'background' | 'text' | 'border' | 'accent' | 'semantic';
  /** Where this color is applied (e.g., ['button', 'card-header']) */
  appliedTo: string[];
  /** Colors that appear adjacent to this one */
  adjacentColors: HSLColor[];
}

/**
 * Hue range for semantic colors
 */
export interface HueRange {
  min: number;
  max: number;
  ideal: number;
}

/**
 * Relationship between two colors
 */
export interface ColorRelationship {
  color1: HSLColor;
  color2: HSLColor;
  type: 'complementary' | 'analogous' | 'triadic' | 'split-complementary' | 'tetradic' | 'monochromatic';
  angle: number; // Degrees of separation on color wheel
  quality: number; // 0-10 score for how well they work together
}

/**
 * Harmony analysis results
 */
export interface HarmonyAnalysis {
  /** Primary harmony type detected */
  type: 'complementary' | 'analogous' | 'triadic' | 'monochromatic' | 'custom';
  /** Quality score 0-10 */
  quality: number;
  /** All color relationships found */
  relationships: ColorRelationship[];
}

/**
 * Contrast validation results
 */
export interface ContrastAnalysis {
  /** WCAG conformance level */
  wcagLevel: 'AAA' | 'AA' | 'fail';
  /** Numeric contrast ratio */
  ratio: number;
  /** Whether it meets requirements for its context */
  meetsRequirements: boolean;
  /** Specific requirements based on context */
  requirements: {
    minimumRatio: number;
    context: string;
  };
}

/**
 * Semantic appropriateness analysis
 */
export interface SemanticAnalysis {
  /** Whether the color fits its semantic role */
  fitsRole: boolean;
  /** Expected hue range for this role */
  expectedRange: HueRange;
  /** Actual hue value */
  actualValue: number;
  /** Confidence in the semantic match (0-1) */
  confidence: number;
  /** Explanation of semantic fit */
  reasoning: string;
}

/**
 * Perceptual appearance analysis (context-dependent)
 */
export interface PerceptionAnalysis {
  /** How the color appears in its context */
  appearsAs: HSLColor;
  /** Perceptual shift from original */
  shift: {
    hue: number;
    saturation: number;
    lightness: number;
  };
  /** Warning about perceptual issues */
  warning?: string;
  /** Albers effect strength (0-1) */
  contextInfluence: number;
}

/**
 * Overall quality assessment
 */
export interface QualityMetrics {
  /** Overall quality score (0-10) */
  score: number;
  /** Sophistication and subtlety (0-10) */
  refinement: number;
  /** Color intensity and energy (0-10) */
  vibrancy: number;
  /** Compositional balance (0-10) */
  balance: number;
  /** Alignment with Swedish aesthetic principles (0-10) */
  aestheticAlignment: number;
}

/**
 * Complete color analysis results
 */
export interface ColorAnalysis {
  /** Color harmony analysis */
  harmony: HarmonyAnalysis;
  /** Contrast validation */
  contrast: ContrastAnalysis;
  /** Semantic appropriateness */
  semantics: SemanticAnalysis;
  /** Perceptual appearance */
  perception: PerceptionAnalysis;
  /** Quality metrics */
  quality: QualityMetrics;
}

/**
 * Impact severity levels
 */
export type ImpactSeverity = 'critical' | 'warning' | 'info';

/**
 * Impact report for color changes
 */
export interface ImpactReport {
  /** Design token affected */
  affectedToken: string;
  /** Severity of the impact */
  severity: ImpactSeverity;
  /** Description of the issue */
  issue: string;
  /** Recommended fix or alternative */
  recommendation?: string;
  /** Specific metrics that failed */
  metrics?: {
    current: number;
    required: number;
    unit: string;
  };
}

/**
 * Main analyzer input
 */
export interface AnalyzerInput {
  originalColor: HSLColor;
  newColor: HSLColor;
  palette: ColorPalette;
  context: UsageContext;
}

/**
 * Main analyzer output
 */
export interface AnalyzerOutput {
  analysis: ColorAnalysis;
  impacts: ImpactReport[];
}

/**
 * Color theory contrast type (Itten's Seven Contrasts)
 */
export type ContrastType =
  | 'hue'           // Pure color contrast
  | 'light-dark'    // Value contrast
  | 'cold-warm'     // Temperature contrast
  | 'complementary' // Opposing colors
  | 'simultaneous'  // Perceptual vibration
  | 'saturation'    // Intensity contrast
  | 'extension';    // Proportion contrast

/**
 * Itten contrast analysis
 */
export interface IttenContrast {
  type: ContrastType;
  strength: number; // 0-1
  description: string;
}

/**
 * Design intent for color adjustments
 * Describes what the user is trying to achieve
 */
export interface DesignIntent {
  /** Primary goal of the color adjustment */
  goal: 'lighten' | 'darken' | 'warm' | 'cool' | 'saturate' | 'desaturate' | 'shift_hue' | 'harmonize';
  /** How much change is desired */
  magnitude: 'subtle' | 'moderate' | 'significant';
  /** Whether to preserve brand colors unchanged */
  preserveBrand?: boolean;
}

/**
 * Quality constraints for suggestions
 * Defines boundaries for acceptable suggestions
 */
export interface QualityConstraints {
  /** Minimum contrast ratio (WCAG AA: 4.5) */
  minimumContrast: number;
  /** Maximum saturation (Swedish aesthetic: 0.8) */
  maxSaturation: number;
  /** Maximum saturation change from original */
  maxSaturationShift: number;
  /** Whether to maintain harmony relationships */
  preserveHarmony: boolean;
  /** Prefer subtle, refined colors (Swedish aesthetic) */
  preferSubtlety: boolean;
  /** Ensure balanced visual weight */
  enforceBalance: boolean;
  /** Token names that cannot be changed */
  lockedColors?: string[];
}

/**
 * A single color change within a palette
 */
export interface ColorChange {
  /** CSS variable/token name */
  token: string;
  /** Original color */
  from: HSLColor;
  /** Suggested new color */
  to: HSLColor;
  /** Explanation for this specific change */
  reason: string;
}

/**
 * Quality scoring for a color suggestion
 */
export interface QualityScore {
  /** Overall quality (0-10) */
  overall: number;
  /** Color harmony quality (0-10) */
  harmony: number;
  /** Contrast accessibility (0-10) */
  contrast: number;
  /** Swedish aesthetic refinement (0-10) */
  refinement: number;
  /** WCAG compliance score (0-10) */
  accessibility: number;
}

/**
 * A complete color palette suggestion
 */
export interface ColorSuggestion {
  /** Unique identifier */
  id: string;
  /** Human-readable name (e.g., "Warmer Variation") */
  name: string;
  /** Brief description of the suggestion */
  description: string;
  /** Complete suggested palette */
  palette: ColorPalette;
  /** List of changes from current palette */
  changes: ColorChange[];
  /** Quality metrics for this suggestion */
  quality: QualityScore;
  /** Detailed explanation using color theory */
  rationale: string;
  /** Optional preview image URL/data */
  preview?: string;
}

/**
 * Harmony variation type
 */
export type HarmonyType = 'complementary' | 'analogous' | 'triadic' | 'monochromatic' | 'split-complementary';

/**
 * Input for the suggestion engine
 */
export interface SuggestionEngineInput {
  /** Current color analysis from analyzer */
  analysis: ColorAnalysis;
  /** Current palette */
  currentPalette: ColorPalette;
  /** User's design intent */
  intent: DesignIntent;
  /** Quality constraints */
  constraints?: QualityConstraints;
  /** Specific color that was changed */
  changedToken?: string;
  /** New value for the changed color */
  changedColor?: HSLColor;
}

/**
 * Output from the suggestion engine
 */
export interface SuggestionEngineOutput {
  /** Ranked list of suggestions (best first) */
  suggestions: ColorSuggestion[];
  /** Execution time in milliseconds */
  executionTime: number;
}