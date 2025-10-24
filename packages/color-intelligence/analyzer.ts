/**
 * Color Analyzer Module
 *
 * Core intelligence for analyzing color changes using color theory principles.
 * Provides comprehensive analysis of harmony, contrast, semantics, and perception.
 */

import type {
  HSLColor,
  ColorPalette,
  UsageContext,
  ColorAnalysis,
  ImpactReport,
  AnalyzerInput,
  AnalyzerOutput,
  HarmonyAnalysis,
  ContrastAnalysis,
  SemanticAnalysis,
  PerceptionAnalysis,
  QualityMetrics,
  ColorRelationship,
} from './types';

import {
  WCAG_REQUIREMENTS,
  SEMANTIC_HUE_RANGES,
  SEMANTIC_SATURATION_RANGES,
  SEMANTIC_LIGHTNESS_RANGES,
  HARMONY_ANGLES,
  SWEDISH_AESTHETIC,
  PERCEPTION_FACTORS,
  QUALITY_WEIGHTS,
} from './constants';

import {
  contrastRatio,
  hueAngle,
  normalizeHue,
  calculateVibrancy,
  calculateRefinement,
  isHueInRange,
  visualWeight,
  areSimilar,
} from './utils';

/**
 * Calculate color harmony relationships
 * Analyzes how colors work together based on color wheel positions
 */
export function calculateHarmony(
  color: HSLColor,
  palette: ColorPalette,
  context: UsageContext
): HarmonyAnalysis {
  const relationships: ColorRelationship[] = [];
  const paletteColors = Object.values(palette);

  // Analyze relationship with each color in palette
  for (const paletteColor of paletteColors) {
    const angle = hueAngle(color.h, paletteColor.h);
    const relationship = identifyRelationshipType(angle);
    const quality = calculateRelationshipQuality(color, paletteColor, relationship);

    relationships.push({
      color1: color,
      color2: paletteColor,
      type: relationship,
      angle,
      quality,
    });
  }

  // Determine dominant harmony type
  const dominantType = findDominantHarmony(relationships);

  // Calculate overall harmony quality
  const harmonyQuality = calculateOverallHarmony(relationships, context);

  return {
    type: dominantType,
    quality: harmonyQuality,
    relationships: relationships.sort((a, b) => b.quality - a.quality),
  };
}

/**
 * Identify the type of color relationship based on hue angle
 */
function identifyRelationshipType(angle: number): ColorRelationship['type'] {
  // Check each harmony type with tolerance
  for (const [type, config] of Object.entries(HARMONY_ANGLES)) {
    const targetAngle = config.angle;
    const tolerance = config.tolerance;

    if (Math.abs(angle - targetAngle) <= tolerance) {
      return type.toLowerCase().replace('_', '-') as ColorRelationship['type'];
    }
  }

  // Special case for split-complementary
  if ((angle >= 150 && angle <= 165) || (angle >= 195 && angle <= 210)) {
    return 'split-complementary';
  }

  return 'monochromatic'; // Default for very similar colors
}

/**
 * Calculate quality score for a color relationship
 */
function calculateRelationshipQuality(
  color1: HSLColor,
  color2: HSLColor,
  type: ColorRelationship['type']
): number {
  let score = 5; // Base score

  // Reward proper harmony relationships
  const angle = hueAngle(color1.h, color2.h);

  switch (type) {
    case 'complementary':
      // Perfect complementary gets bonus
      score += (1 - Math.abs(180 - angle) / 15) * 3;
      break;
    case 'analogous':
      // Analogous works best with similar saturation/lightness
      const satDiff = Math.abs(color1.s - color2.s);
      const lightDiff = Math.abs(color1.l - color2.l);
      score += (1 - satDiff / 50) * 1.5;
      score += (1 - lightDiff / 50) * 1.5;
      break;
    case 'triadic':
      score += (1 - Math.abs(120 - angle) / 15) * 2.5;
      break;
    case 'monochromatic':
      // Monochromatic needs good contrast in saturation or lightness
      const contrast = Math.abs(color1.s - color2.s) + Math.abs(color1.l - color2.l);
      score += Math.min(contrast / 30, 3);
      break;
  }

  // Swedish aesthetic bonus for subtle, refined combinations
  if (color1.s < 70 && color2.s < 70) {
    score += 0.5; // Subtle saturation
  }

  // Penalize very high saturation combinations
  if (color1.s > 85 && color2.s > 85) {
    score -= 1;
  }

  return Math.min(Math.max(score, 0), 10);
}

/**
 * Find the dominant harmony type in a set of relationships
 */
function findDominantHarmony(relationships: ColorRelationship[]): HarmonyAnalysis['type'] {
  const typeCounts = new Map<ColorRelationship['type'], number>();

  for (const rel of relationships) {
    if (rel.quality > 6) { // Only count good relationships
      typeCounts.set(rel.type, (typeCounts.get(rel.type) || 0) + rel.quality);
    }
  }

  // Find type with highest weighted count
  let dominant: HarmonyAnalysis['type'] = 'custom';
  let maxScore = 0;

  for (const [type, score] of typeCounts.entries()) {
    if (score > maxScore) {
      maxScore = score;
      dominant = type as HarmonyAnalysis['type'];
    }
  }

  return dominant;
}

/**
 * Calculate overall harmony quality score
 */
function calculateOverallHarmony(relationships: ColorRelationship[], context: UsageContext): number {
  if (relationships.length === 0) return 5;

  // Consider relationships with adjacent colors more heavily
  const adjacentRelationships = relationships.filter(rel =>
    context.adjacentColors.some(adj => areSimilar(adj, rel.color2))
  );

  const relevantRels = adjacentRelationships.length > 0 ? adjacentRelationships : relationships;

  // Average of top relationships
  const topRels = relevantRels.slice(0, 5);
  const avgQuality = topRels.reduce((sum, rel) => sum + rel.quality, 0) / topRels.length;

  return Math.round(avgQuality * 10) / 10;
}

/**
 * Validate contrast ratios for accessibility
 */
export function validateContrast(
  color: HSLColor,
  palette: ColorPalette,
  context: UsageContext
): ContrastAnalysis {
  // Determine what we need to check contrast against
  const checkAgainst = getContrastTargets(context, palette);

  let worstRatio = Infinity;
  let requirements = { minimumRatio: 0, context: '' };

  for (const target of checkAgainst) {
    const ratio = contrastRatio(color, target.color);

    if (ratio < worstRatio) {
      worstRatio = ratio;
      requirements = {
        minimumRatio: target.minRatio,
        context: target.context,
      };
    }
  }

  // Determine WCAG level
  let wcagLevel: ContrastAnalysis['wcagLevel'] = 'fail';

  if (worstRatio >= WCAG_REQUIREMENTS.NORMAL_TEXT.AAA) {
    wcagLevel = 'AAA';
  } else if (worstRatio >= WCAG_REQUIREMENTS.NORMAL_TEXT.AA) {
    wcagLevel = 'AA';
  } else if (worstRatio >= WCAG_REQUIREMENTS.UI_COMPONENTS.AA && context.role !== 'text') {
    wcagLevel = 'AA';
  }

  return {
    wcagLevel,
    ratio: Math.round(worstRatio * 100) / 100,
    meetsRequirements: worstRatio >= requirements.minimumRatio,
    requirements,
  };
}

/**
 * Determine which colors to check contrast against
 */
function getContrastTargets(
  context: UsageContext,
  palette: ColorPalette
): Array<{ color: HSLColor; minRatio: number; context: string }> {
  const targets = [];

  switch (context.role) {
    case 'text':
      // Text must contrast with backgrounds
      targets.push(
        { color: palette.background, minRatio: WCAG_REQUIREMENTS.NORMAL_TEXT.AA, context: 'text on background' },
        { color: palette.surface, minRatio: WCAG_REQUIREMENTS.NORMAL_TEXT.AA, context: 'text on surface' }
      );
      break;

    case 'background':
      // Background must contrast with text
      targets.push(
        { color: palette.text, minRatio: WCAG_REQUIREMENTS.NORMAL_TEXT.AA, context: 'background under text' },
        { color: palette.textMuted, minRatio: WCAG_REQUIREMENTS.NORMAL_TEXT.AA, context: 'background under muted text' }
      );
      break;

    case 'border':
      // Borders need 3:1 against adjacent surfaces
      targets.push(
        { color: palette.background, minRatio: WCAG_REQUIREMENTS.UI_COMPONENTS.AA, context: 'border on background' },
        { color: palette.surface, minRatio: WCAG_REQUIREMENTS.UI_COMPONENTS.AA, context: 'border on surface' }
      );
      break;

    case 'accent':
    case 'semantic':
      // Semantic colors often appear as text or important UI
      targets.push(
        { color: palette.background, minRatio: WCAG_REQUIREMENTS.NORMAL_TEXT.AA, context: 'accent on background' },
        { color: palette.surface, minRatio: WCAG_REQUIREMENTS.UI_COMPONENTS.AA, context: 'accent on surface' }
      );
      break;
  }

  // Also check against adjacent colors if provided
  for (const adjacent of context.adjacentColors) {
    targets.push({
      color: adjacent,
      minRatio: WCAG_REQUIREMENTS.UI_COMPONENTS.AA,
      context: 'adjacent color',
    });
  }

  return targets;
}

/**
 * Assess semantic appropriateness of a color
 */
export function assessSemantics(
  color: HSLColor,
  context: UsageContext
): SemanticAnalysis {
  // Only assess semantic colors
  if (context.role !== 'semantic') {
    return {
      fitsRole: true,
      expectedRange: { min: 0, max: 360, ideal: color.h },
      actualValue: color.h,
      confidence: 1.0,
      reasoning: 'Non-semantic color, no specific requirements',
    };
  }

  // Determine semantic type from context
  const semanticType = detectSemanticType(context.appliedTo);

  if (!semanticType) {
    return {
      fitsRole: true,
      expectedRange: { min: 0, max: 360, ideal: color.h },
      actualValue: color.h,
      confidence: 0.5,
      reasoning: 'Could not determine specific semantic role',
    };
  }

  const hueRange = SEMANTIC_HUE_RANGES[semanticType];
  const satRange = SEMANTIC_SATURATION_RANGES[semanticType];
  const lightRange = SEMANTIC_LIGHTNESS_RANGES[semanticType];

  // Check if color fits expected ranges
  const hueFits = isHueInRange(color.h, hueRange.min, hueRange.max);
  const satFits = color.s >= satRange.min && color.s <= satRange.max;
  const lightFits = color.l >= lightRange.min && color.l <= lightRange.max;

  // Calculate confidence based on how well it fits
  let confidence = 0;

  if (hueFits) {
    const hueDistance = Math.min(
      Math.abs(color.h - hueRange.ideal),
      360 - Math.abs(color.h - hueRange.ideal)
    );
    confidence += (1 - hueDistance / 180) * 0.5; // Hue is 50% of confidence
  }

  if (satFits) {
    const satDistance = Math.abs(color.s - satRange.ideal);
    confidence += (1 - satDistance / 50) * 0.25; // Saturation is 25%
  }

  if (lightFits) {
    const lightDistance = Math.abs(color.l - lightRange.ideal);
    confidence += (1 - lightDistance / 50) * 0.25; // Lightness is 25%
  }

  const fitsRole = hueFits && confidence > 0.6;

  // Generate reasoning
  let reasoning = `${semanticType} color: `;
  if (fitsRole) {
    reasoning += 'Color fits semantic expectations well';
  } else {
    const issues = [];
    if (!hueFits) issues.push(`hue should be ${hueRange.min}-${hueRange.max}°`);
    if (!satFits) issues.push(`saturation should be ${satRange.min}-${satRange.max}%`);
    if (!lightFits) issues.push(`lightness should be ${lightRange.min}-${lightRange.max}%`);
    reasoning += issues.join(', ');
  }

  return {
    fitsRole,
    expectedRange: hueRange,
    actualValue: color.h,
    confidence: Math.round(confidence * 100) / 100,
    reasoning,
  };
}

/**
 * Detect semantic type from usage context
 */
function detectSemanticType(appliedTo: string[]): string | null {
  const keywords = {
    success: ['success', 'confirm', 'complete', 'valid', 'approved'],
    warning: ['warning', 'caution', 'alert', 'pending'],
    error: ['error', 'fail', 'invalid', 'danger', 'critical'],
    info: ['info', 'information', 'note', 'hint', 'help'],
    primary: ['primary', 'main', 'brand', 'action', 'cta'],
  };

  for (const [type, words] of Object.entries(keywords)) {
    if (appliedTo.some(usage =>
      words.some(word => usage.toLowerCase().includes(word))
    )) {
      return type;
    }
  }

  return null;
}

/**
 * Predict how color appears in context (Albers principle)
 */
export function predictPerception(
  color: HSLColor,
  context: UsageContext
): PerceptionAnalysis {
  if (context.adjacentColors.length === 0) {
    return {
      appearsAs: color,
      shift: { hue: 0, saturation: 0, lightness: 0 },
      contextInfluence: 0,
    };
  }

  // Calculate perceptual shifts based on adjacent colors
  let hueShift = 0;
  let satShift = 0;
  let lightShift = 0;
  let totalInfluence = 0;

  for (let i = 0; i < context.adjacentColors.length; i++) {
    const adjacent = context.adjacentColors[i];
    const influence = i === 0
      ? PERCEPTION_FACTORS.ADJACENT_INFLUENCE.immediate
      : PERCEPTION_FACTORS.ADJACENT_INFLUENCE.near;

    // Simultaneous contrast effects
    // Colors appear shifted away from adjacent colors
    const hueDiff = hueAngle(color.h, adjacent.h);
    if (hueDiff < 90) {
      // Push hue away from similar adjacent hue
      hueShift += (hueDiff < 45 ? -1 : 1) * influence * 10;
    }

    // Lightness contrast
    const lightDiff = color.l - adjacent.l;
    if (Math.abs(lightDiff) < 30) {
      // Enhance contrast when similar
      lightShift += (lightDiff > 0 ? 1 : -1) * influence * 5;
    }

    // Saturation interaction
    if (adjacent.s > 70 && color.s < 50) {
      // Appears less saturated next to vibrant colors
      satShift -= influence * 10;
    } else if (adjacent.s < 30 && color.s > 50) {
      // Appears more saturated next to muted colors
      satShift += influence * 5;
    }

    totalInfluence += influence;
  }

  // Apply maximum shift limits
  hueShift = Math.max(-PERCEPTION_FACTORS.MAX_HUE_SHIFT,
    Math.min(PERCEPTION_FACTORS.MAX_HUE_SHIFT, hueShift));
  satShift = Math.max(-PERCEPTION_FACTORS.MAX_SATURATION_SHIFT,
    Math.min(PERCEPTION_FACTORS.MAX_SATURATION_SHIFT, satShift));
  lightShift = Math.max(-PERCEPTION_FACTORS.MAX_LIGHTNESS_SHIFT,
    Math.min(PERCEPTION_FACTORS.MAX_LIGHTNESS_SHIFT, lightShift));

  const appearsAs: HSLColor = {
    h: normalizeHue(color.h + hueShift),
    s: Math.max(0, Math.min(100, color.s + satShift)),
    l: Math.max(0, Math.min(100, color.l + lightShift)),
    a: color.a,
  };

  // Generate warning if significant shift
  let warning: string | undefined;
  if (Math.abs(lightShift) > 10) {
    warning = `May appear ${lightShift > 0 ? 'lighter' : 'darker'} due to adjacent colors`;
  } else if (Math.abs(satShift) > 15) {
    warning = `May appear ${satShift > 0 ? 'more vibrant' : 'more muted'} in this context`;
  }

  return {
    appearsAs,
    shift: {
      hue: Math.round(hueShift * 10) / 10,
      saturation: Math.round(satShift * 10) / 10,
      lightness: Math.round(lightShift * 10) / 10,
    },
    warning,
    contextInfluence: Math.min(totalInfluence, 1),
  };
}

/**
 * Calculate overall quality metrics
 */
function calculateQualityMetrics(
  color: HSLColor,
  analysis: Partial<ColorAnalysis>
): QualityMetrics {
  const vibrancy = calculateVibrancy(color);
  const refinement = calculateRefinement(color);

  // Balance based on visual weight distribution
  const balance = calculateBalance(color, analysis.harmony?.relationships || []);

  // Swedish aesthetic alignment
  const aestheticAlignment = calculateAestheticAlignment(color, refinement, vibrancy);

  // Overall score weighted by different factors
  const score =
    (analysis.harmony?.quality || 5) * QUALITY_WEIGHTS.HARMONY +
    (analysis.contrast?.wcagLevel === 'AAA' ? 10 :
     analysis.contrast?.wcagLevel === 'AA' ? 8 : 5) * QUALITY_WEIGHTS.CONTRAST +
    (analysis.semantics?.fitsRole ? 9 : 5) * QUALITY_WEIGHTS.SEMANTICS +
    refinement * QUALITY_WEIGHTS.REFINEMENT +
    balance * QUALITY_WEIGHTS.BALANCE;

  return {
    score: Math.round(score * 10) / 10,
    refinement: Math.round(refinement * 10) / 10,
    vibrancy: Math.round(vibrancy * 10) / 10,
    balance: Math.round(balance * 10) / 10,
    aestheticAlignment: Math.round(aestheticAlignment * 10) / 10,
  };
}

/**
 * Calculate color balance in composition
 */
function calculateBalance(color: HSLColor, relationships: ColorRelationship[]): number {
  if (relationships.length === 0) return 7;

  // Check weight distribution
  const weights = relationships.map(rel => visualWeight(rel.color2));
  const avgWeight = weights.reduce((a, b) => a + b, 0) / weights.length;
  const colorWeight = visualWeight(color);

  // Good balance means not too different from average
  const weightDiff = Math.abs(colorWeight - avgWeight);
  const balanceScore = Math.max(0, 10 - weightDiff);

  return balanceScore;
}

/**
 * Calculate alignment with Swedish aesthetic principles
 */
function calculateAestheticAlignment(
  color: HSLColor,
  refinement: number,
  vibrancy: number
): number {
  let score = 5;

  // Prefer refined colors
  if (refinement > 7) score += 2;

  // Moderate vibrancy is ideal
  if (vibrancy >= 3 && vibrancy <= 7) score += 1.5;

  // Check against Swedish aesthetic ranges
  if (color.s >= SWEDISH_AESTHETIC.SATURATION.min &&
      color.s <= SWEDISH_AESTHETIC.SATURATION.max) {
    score += 1;
  }

  if (color.l >= SWEDISH_AESTHETIC.LIGHTNESS.min &&
      color.l <= SWEDISH_AESTHETIC.LIGHTNESS.max) {
    score += 0.5;
  }

  return Math.min(score, 10);
}

/**
 * Generate impact reports for color changes
 */
function generateImpactReports(
  input: AnalyzerInput,
  analysis: ColorAnalysis
): ImpactReport[] {
  const impacts: ImpactReport[] = [];

  // Check contrast issues
  if (!analysis.contrast.meetsRequirements) {
    impacts.push({
      affectedToken: `${input.context.role}-color`,
      severity: 'critical',
      issue: `Contrast ratio ${analysis.contrast.ratio} is below required ${analysis.contrast.requirements.minimumRatio}`,
      recommendation: `Adjust lightness to achieve at least ${analysis.contrast.requirements.minimumRatio}:1 contrast`,
      metrics: {
        current: analysis.contrast.ratio,
        required: analysis.contrast.requirements.minimumRatio,
        unit: ':1',
      },
    });
  }

  // Check semantic issues
  if (!analysis.semantics.fitsRole && analysis.semantics.confidence < 0.5) {
    impacts.push({
      affectedToken: `${input.context.role}-semantic`,
      severity: 'warning',
      issue: analysis.semantics.reasoning,
      recommendation: `Consider hue closer to ${analysis.semantics.expectedRange.ideal}°`,
      metrics: {
        current: analysis.semantics.actualValue,
        required: analysis.semantics.expectedRange.ideal,
        unit: '°',
      },
    });
  }

  // Check harmony issues
  if (analysis.harmony.quality < 6) {
    impacts.push({
      affectedToken: 'color-harmony',
      severity: 'info',
      issue: 'Color harmony could be improved',
      recommendation: 'Consider adjusting hue to create stronger color relationships',
    });
  }

  // Check perception warnings
  if (analysis.perception.warning) {
    impacts.push({
      affectedToken: 'color-perception',
      severity: 'info',
      issue: analysis.perception.warning,
      recommendation: 'Consider testing in context to verify appearance',
    });
  }

  // Check quality threshold
  if (analysis.quality.score < SWEDISH_AESTHETIC.QUALITY.minimum) {
    impacts.push({
      affectedToken: 'quality-score',
      severity: 'warning',
      issue: `Quality score ${analysis.quality.score} is below minimum ${SWEDISH_AESTHETIC.QUALITY.minimum}`,
      recommendation: 'Refine color choice for better aesthetic alignment',
      metrics: {
        current: analysis.quality.score,
        required: SWEDISH_AESTHETIC.QUALITY.minimum,
        unit: '/10',
      },
    });
  }

  return impacts;
}

/**
 * Main color analyzer function
 * Performs comprehensive color analysis in <5ms
 */
export function analyzeColor(input: AnalyzerInput): AnalyzerOutput {
  const startTime = performance.now();

  // Run all analysis functions
  const harmony = calculateHarmony(input.newColor, input.palette, input.context);
  const contrast = validateContrast(input.newColor, input.palette, input.context);
  const semantics = assessSemantics(input.newColor, input.context);
  const perception = predictPerception(input.newColor, input.context);

  // Build complete analysis
  const analysis: ColorAnalysis = {
    harmony,
    contrast,
    semantics,
    perception,
    quality: calculateQualityMetrics(input.newColor, {
      harmony,
      contrast,
      semantics,
      perception,
    }),
  };

  // Generate impact reports
  const impacts = generateImpactReports(input, analysis);

  // Performance check
  const elapsed = performance.now() - startTime;
  if (elapsed > 5) {
    console.warn(`Color analysis took ${elapsed.toFixed(2)}ms (target: <5ms)`);
  }

  return {
    analysis,
    impacts,
  };
}

// Export all public functions
export {
  calculateQualityMetrics,
  generateImpactReports,
};