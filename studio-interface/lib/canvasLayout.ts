/**
 * Canvas Layout System
 * Handles automatic organization of canvas artifacts based on AI instructions
 */

import type { CanvasArtifact } from '@/state/store'

export interface LayoutZone {
  label: string
  x: number
  y: number
  artifacts: string[] // Array of artifact IDs
}

export interface LayoutInstructions {
  action: 'organize'
  reasoning?: string
  zones: Record<string, LayoutZone>
}

/**
 * Organize artifacts into zones based on layout instructions from AI
 */
export function organizeArtifacts(
  artifacts: CanvasArtifact[],
  instructions: LayoutInstructions
): Array<{ id: string; position: { x: number; y: number } }> {
  const updates: Array<{ id: string; position: { x: number; y: number } }> = []

  // Process each zone and position its artifacts
  Object.entries(instructions.zones).forEach(([zoneName, zone]) => {
    // Get artifacts for this zone
    const zoneArtifacts = artifacts.filter(artifact =>
      zone.artifacts.includes(artifact.id)
    )

    // Calculate positions for artifacts in this zone
    zoneArtifacts.forEach((artifact, index) => {
      const position = calculateZonePosition(zone, index, zoneArtifacts.length)
      updates.push({
        id: artifact.id,
        position,
      })
    })
  })

  return updates
}

/**
 * Calculate position for an artifact within a zone
 */
function calculateZonePosition(
  zone: LayoutZone,
  index: number,
  totalCount: number
): { x: number; y: number } {
  const spacing = 40 // Increased spacing
  const cardWidth = 280
  const cardHeight = 180

  // Vertical stack layout within zone (easier to scan)
  return {
    x: zone.x,
    y: zone.y + index * (cardHeight + spacing),
  }
}

/**
 * Create default cluster layout
 * Useful fallback when AI doesn't provide specific instructions
 */
export function createClusterLayout(artifacts: CanvasArtifact[]): LayoutInstructions {
  return {
    action: 'organize',
    layout: 'clusters',
    zones: {
      media: {
        x: 80,
        y: 80,
        artifactTypes: ['link-card', 'asset-collection'],
      },
      people: {
        x: 900,
        y: 80,
        artifactTypes: ['research-panel'],
      },
      notes: {
        x: 80,
        y: 800,
        artifactTypes: ['sticky-note', 'strategy-card'],
      },
    },
  }
}
