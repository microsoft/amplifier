/**
 * Entity Extraction System
 * Detects URLs, entities, strategies, and other meaningful content
 * Triggers canvas artifact creation with smart placement
 */

import type { CanvasArtifact } from '@/state/store'
import { calculateNextPosition, ARTIFACT_SIZES, type Point } from '@/utils/smartPlacement'

export interface ExtractionResult {
  type: CanvasArtifact['type']
  data: CanvasArtifact['data']
  position: { x: number; y: number }
  visible: boolean
}

/**
 * Extract URLs from message
 */
export function extractURLs(message: string): ExtractionResult[] {
  const urlRegex = /https?:\/\/[^\s]+/g
  const urls = message.match(urlRegex) || []

  return urls.map((url, index) => ({
    type: 'link-card' as const,
    data: {
      url,
      title: 'Loading...',
      description: '',
      loading: true,
    },
    position: calculatePosition('link-card', index),
    visible: true,
  }))
}

/**
 * Extract named entities (people, places, brands)
 * Simple pattern matching - can be enhanced with NLP
 */
export function extractNamedEntities(message: string): ExtractionResult[] {
  const entities: ExtractionResult[] = []

  // Pattern 1: List format with dash/bullet (e.g., "- Paul Thiry")
  const listPattern = /^[\s-•*]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)(?:\s*\(|$)/gm
  const listMatches = Array.from(message.matchAll(listPattern))
  const listEntities = listMatches.map(match => match[1].trim())

  // Pattern 2: Standard capitalized words (2-4 words) that might be names
  const namePattern = /\b([A-Z][a-z]+(?:\s+[A-Z][a-z]+){1,3})\b/g
  const nameMatches = message.match(namePattern) || []

  // Combine both patterns
  const allMatches = [...listEntities, ...nameMatches]

  // Filter out common false positives
  const commonWords = new Set(['I', 'The', 'A', 'An', 'This', 'That', 'Would', 'Could', 'Should'])
  const validEntities = allMatches.filter(
    (match) => !commonWords.has(match) && match.split(' ').length >= 2
  )

  // Deduplicate
  const uniqueEntities = Array.from(new Set(validEntities))

  return uniqueEntities.map((entity, index) => ({
    type: 'research-panel' as const,
    data: {
      entity,
      bio: '',
      images: [],
      articles: [],
      loading: true,
    },
    position: calculatePosition('research-panel', index),
    visible: true,
  }))
}

/**
 * Extract strategy/goal statements
 */
export function extractStrategies(message: string): ExtractionResult[] {
  const strategies: ExtractionResult[] = []

  // Pattern: "I need/want to..." or "It will be..."
  const strategyPatterns = [
    /I (?:need|want|plan) to ([^.!?]+)/gi,
    /It will be ([^.!?]+)/gi,
    /We'll be (?:using|creating|building) ([^.!?]+)/gi,
  ]

  strategyPatterns.forEach((pattern) => {
    const matches = Array.from(message.matchAll(pattern))
    matches.forEach((match, index) => {
      const strategy = match[1].trim()
      if (strategy.length > 10) {
        // Meaningful strategy
        strategies.push({
          type: 'sticky-note' as const,
          data: {
            note: strategy,
            color: pickNoteColor(strategies.length + index),
          },
          position: calculatePosition('sticky-note', strategies.length + index),
          visible: true,
        })
      }
    })
  })

  return strategies
}

/**
 * Extract channel/platform mentions
 */
export function extractChannels(message: string): ExtractionResult[] {
  const channels: ExtractionResult[] = []

  const channelKeywords = {
    'dedicated site': 'Content Hub',
    website: 'Content Hub',
    airbnb: 'Airbnb / STR',
    'short term rental': 'STR Platform',
    str: 'STR Platform',
    'social media': 'Social Distribution',
    instagram: 'Instagram',
    facebook: 'Facebook',
    twitter: 'Twitter',
    blog: 'Blog',
  }

  const lowerMessage = message.toLowerCase()

  Object.entries(channelKeywords).forEach(([keyword, channelName], index) => {
    if (lowerMessage.includes(keyword)) {
      // Avoid duplicates
      const exists = channels.some((c) => c.data.channel === channelName)
      if (!exists) {
        channels.push({
          type: 'strategy-card' as const,
          data: {
            strategy: channelName,
            channel: channelName,
            goals: [],
          },
          position: calculatePosition('strategy-card', channels.length),
          visible: true,
        })
      }
    }
  })

  return channels
}

/**
 * Main extraction function - runs all extractors
 */
export function extractEntities(message: string): ExtractionResult[] {
  const results: ExtractionResult[] = []

  // Reset position tracking for new extraction batch
  resetExtractionPositions()

  // Run all extractors
  results.push(...extractURLs(message))
  results.push(...extractNamedEntities(message))
  results.push(...extractStrategies(message))
  results.push(...extractChannels(message))

  return results
}

/**
 * Calculate position for new artifact
 * Simple auto-layout - can be enhanced with more sophisticated layout
 */
// Track existing positions for current extraction batch
let extractionPositions: Array<{ position: Point; size?: { width: number; height: number } }> = []

// Store reference to existing canvas artifacts (passed from component)
let existingCanvasArtifacts: Array<{ position: Point; size?: { width: number; height: number } }> = []

function calculatePosition(
  type: CanvasArtifact['type'],
  index: number
): { x: number; y: number } {
  // Use smart placement with spiral strategy for extracted entities
  const canvasBounds = {
    x: 0,
    y: 0,
    width: 2000,  // Virtual canvas size
    height: 2000,
  }

  // Combine existing canvas artifacts with newly extracted positions
  const allExistingArtifacts = [...existingCanvasArtifacts, ...extractionPositions]

  const position = calculateNextPosition({
    strategy: 'spiral',  // Use spiral for programmatic additions
    canvasBounds,
    existingArtifacts: allExistingArtifacts,
    artifactSize: ARTIFACT_SIZES[type] || ARTIFACT_SIZES.default,
    gridSize: 40
  })

  // Track this position for next calculation in this batch
  extractionPositions.push({
    position,
    size: ARTIFACT_SIZES[type] || ARTIFACT_SIZES.default
  })

  return position
}

// Set existing canvas artifacts for smart placement
export function setExistingArtifacts(artifacts: CanvasArtifact[]) {
  existingCanvasArtifacts = artifacts
    .filter(a => a.visible)
    .map(a => ({
      position: a.position,
      size: ARTIFACT_SIZES[a.type] || ARTIFACT_SIZES.default
    }))
}

// Reset positions when starting new extraction batch
export function resetExtractionPositions() {
  extractionPositions = []
}

/**
 * Pick color for sticky note
 */
function pickNoteColor(index: number): string {
  const colors = [
    '#FEF3C7', // Yellow
    '#DBEAFE', // Blue
    '#D1FAE5', // Green
    '#FCE7F3', // Pink
    '#E0E7FF', // Indigo
  ]

  return colors[index % colors.length]
}

/**
 * Fetch metadata for URL (to be called after initial extraction)
 */
export async function fetchURLMetadata(url: string): Promise<{
  title: string
  description: string
  image: string
  favicon: string
}> {
  try {
    // TODO: Implement actual metadata fetching
    // Options:
    // 1. Use opengraph-io or similar service
    // 2. Use custom scraping endpoint
    // 3. Use browser extension APIs

    // For now, return mock data
    return {
      title: new URL(url).hostname,
      description: 'Link preview',
      image: '',
      favicon: `https://www.google.com/s2/favicons?domain=${new URL(url).hostname}`,
    }
  } catch (error) {
    console.error('Failed to fetch URL metadata:', error)
    return {
      title: url,
      description: '',
      image: '',
      favicon: '',
    }
  }
}

/**
 * Search for entity information (to be called after initial extraction)
 */
export async function searchEntityInfo(entity: string): Promise<{
  bio: string
  images: string[]
  articles: Array<{ title: string; url: string }>
}> {
  try {
    // TODO: Implement actual entity search
    // Options:
    // 1. Wikipedia API
    // 2. Google Custom Search
    // 3. DuckDuckGo Instant Answer API
    // 4. Custom scraping

    // For now, return mock data
    return {
      bio: `Information about ${entity}...`,
      images: [],
      articles: [],
    }
  } catch (error) {
    console.error('Failed to search entity:', error)
    return {
      bio: '',
      images: [],
      articles: [],
    }
  }
}
