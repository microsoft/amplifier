/**
 * Smart Placement Algorithm for Canvas Artifacts
 *
 * Three strategies:
 * 1. Spiral - Organic, gallery-like arrangement from center
 * 2. Proximity - Places near target point, avoiding overlaps
 * 3. Grid - Clean rows and columns with consistent spacing
 */

export interface Point {
  x: number
  y: number
}

export interface Size {
  width: number
  height: number
}

export interface Rect {
  x: number
  y: number
  width: number
  height: number
}

export type PlacementStrategy = 'spiral' | 'proximity' | 'grid'

export interface PlacementOptions {
  strategy: PlacementStrategy
  canvasBounds: Rect
  existingArtifacts: Array<{ position: Point; size?: Size }>
  targetPoint?: Point  // For proximity strategy
  artifactSize?: Size  // Size of artifact being placed
  gridSize?: number  // Default 40px
}

// Constants for placement algorithms
const GOLDEN_RATIO = 1.618033988749895
const GOLDEN_ANGLE = 137.5077640500378  // degrees
const SPIRAL_RADIUS_STEP = 80  // pixels per revolution
const GRID_GUTTER_H = 48  // horizontal spacing
const GRID_GUTTER_V = 64  // vertical spacing
const DEFAULT_GRID_SIZE = 40
const DEFAULT_ARTIFACT_SIZE: Size = { width: 280, height: 200 }

// Helper function to check if two rectangles collide
function checkCollision(rect1: Rect, rect2: Rect): boolean {
  return !(
    rect1.x + rect1.width < rect2.x ||
    rect2.x + rect2.width < rect1.x ||
    rect1.y + rect1.height < rect2.y ||
    rect2.y + rect2.height < rect1.y
  )
}

// Helper to snap a point to grid
function snapToGrid(point: Point, gridSize: number): Point {
  return {
    x: Math.round(point.x / gridSize) * gridSize,
    y: Math.round(point.y / gridSize) * gridSize
  }
}

// Get center point of a rectangle
function getCanvasCenter(bounds: Rect): Point {
  return {
    x: bounds.x + bounds.width / 2,
    y: bounds.y + bounds.height / 2
  }
}

// Check if a position would cause collision with existing artifacts
function wouldCollide(
  position: Point,
  size: Size,
  existingArtifacts: Array<{ position: Point; size?: Size }>
): boolean {
  const newRect: Rect = {
    x: position.x,
    y: position.y,
    width: size.width,
    height: size.height
  }

  for (const artifact of existingArtifacts) {
    const artifactRect: Rect = {
      x: artifact.position.x,
      y: artifact.position.y,
      width: artifact.size?.width || DEFAULT_ARTIFACT_SIZE.width,
      height: artifact.size?.height || DEFAULT_ARTIFACT_SIZE.height
    }

    if (checkCollision(newRect, artifactRect)) {
      return true
    }
  }

  return false
}

// Spiral placement algorithm
function spiralPlacement(options: PlacementOptions): Point {
  const center = getCanvasCenter(options.canvasBounds)
  const artifactSize = options.artifactSize || DEFAULT_ARTIFACT_SIZE
  const gridSize = options.gridSize || DEFAULT_GRID_SIZE

  // Start from center
  if (options.existingArtifacts.length === 0) {
    return snapToGrid(center, gridSize)
  }

  // Generate spiral points
  let angle = 0
  let radius = 0
  const angleStep = GOLDEN_ANGLE * (Math.PI / 180)  // Convert to radians

  // Try increasingly distant points in the spiral
  for (let i = 0; i < 100; i++) {  // Max 100 attempts
    // Calculate position using golden spiral
    const x = center.x + radius * Math.cos(angle)
    const y = center.y + radius * Math.sin(angle)

    const position = snapToGrid({ x, y }, gridSize)

    // Check if position is within bounds
    if (position.x < options.canvasBounds.x ||
        position.y < options.canvasBounds.y ||
        position.x + artifactSize.width > options.canvasBounds.x + options.canvasBounds.width ||
        position.y + artifactSize.height > options.canvasBounds.y + options.canvasBounds.height) {
      // Continue spiral
      angle += angleStep
      radius += SPIRAL_RADIUS_STEP / (2 * Math.PI)  // Gradual radius increase
      continue
    }

    // Check for collisions
    if (!wouldCollide(position, artifactSize, options.existingArtifacts)) {
      return position
    }

    // Move to next point in spiral
    angle += angleStep
    radius += SPIRAL_RADIUS_STEP / (2 * Math.PI)
  }

  // Fallback: place at bottom-right of existing artifacts
  const lastArtifact = options.existingArtifacts[options.existingArtifacts.length - 1]
  return snapToGrid({
    x: lastArtifact.position.x + (lastArtifact.size?.width || DEFAULT_ARTIFACT_SIZE.width) + GRID_GUTTER_H,
    y: lastArtifact.position.y
  }, gridSize)
}

// Proximity placement algorithm - finds nearest empty spot to target
function proximityPlacement(options: PlacementOptions): Point {
  const targetPoint = options.targetPoint || getCanvasCenter(options.canvasBounds)
  const artifactSize = options.artifactSize || DEFAULT_ARTIFACT_SIZE
  const gridSize = options.gridSize || DEFAULT_GRID_SIZE

  // Start from target point
  const snappedTarget = snapToGrid(targetPoint, gridSize)

  // Check if target position is valid
  if (!wouldCollide(snappedTarget, artifactSize, options.existingArtifacts)) {
    return snappedTarget
  }

  // Search in expanding circles
  const maxRadius = Math.max(options.canvasBounds.width, options.canvasBounds.height)

  for (let radius = gridSize; radius < maxRadius; radius += gridSize) {
    // Check points in a circle around target
    const numPoints = Math.max(8, Math.floor((2 * Math.PI * radius) / gridSize))

    for (let i = 0; i < numPoints; i++) {
      const angle = (2 * Math.PI * i) / numPoints
      const x = targetPoint.x + radius * Math.cos(angle)
      const y = targetPoint.y + radius * Math.sin(angle)

      const position = snapToGrid({ x, y }, gridSize)

      // Check bounds
      if (position.x < options.canvasBounds.x ||
          position.y < options.canvasBounds.y ||
          position.x + artifactSize.width > options.canvasBounds.x + options.canvasBounds.width ||
          position.y + artifactSize.height > options.canvasBounds.y + options.canvasBounds.height) {
        continue
      }

      // Check collisions
      if (!wouldCollide(position, artifactSize, options.existingArtifacts)) {
        return position
      }
    }
  }

  // Fallback: use spiral placement
  return spiralPlacement(options)
}

// Smart grid placement algorithm
function gridPlacement(options: PlacementOptions): Point {
  const artifactSize = options.artifactSize || DEFAULT_ARTIFACT_SIZE
  const gridSize = options.gridSize || DEFAULT_GRID_SIZE

  // Calculate optimal columns based on canvas width
  const effectiveWidth = options.canvasBounds.width - (2 * GRID_GUTTER_H)  // Margins
  const colWidth = artifactSize.width + GRID_GUTTER_H
  const numColumns = Math.max(1, Math.floor(effectiveWidth / colWidth))

  // Starting position (with margins)
  const startX = options.canvasBounds.x + GRID_GUTTER_H
  const startY = options.canvasBounds.y + GRID_GUTTER_V

  // Find first empty grid cell
  for (let row = 0; row < 100; row++) {  // Max 100 rows
    for (let col = 0; col < numColumns; col++) {
      const x = startX + (col * (artifactSize.width + GRID_GUTTER_H))
      const y = startY + (row * (artifactSize.height + GRID_GUTTER_V))

      const position = snapToGrid({ x, y }, gridSize)

      // Check bounds
      if (position.y + artifactSize.height > options.canvasBounds.y + options.canvasBounds.height) {
        // Exceeded canvas height
        break
      }

      // Check for collisions
      if (!wouldCollide(position, artifactSize, options.existingArtifacts)) {
        return position
      }
    }
  }

  // Fallback: place at end
  const lastY = startY + (100 * (artifactSize.height + GRID_GUTTER_V))
  return snapToGrid({ x: startX, y: lastY }, gridSize)
}

// Main function to calculate next position
export function calculateNextPosition(options: PlacementOptions): Point {
  switch (options.strategy) {
    case 'spiral':
      return spiralPlacement(options)

    case 'proximity':
      return proximityPlacement(options)

    case 'grid':
      return gridPlacement(options)

    default:
      // Default to spiral
      return spiralPlacement(options)
  }
}

// Export helper functions for potential reuse
export {
  checkCollision,
  snapToGrid,
  getCanvasCenter,
  wouldCollide
}

// Artifact size constants
export const ARTIFACT_SIZES = {
  'link-card': { width: 280, height: 200 },
  'sticky-note': { width: 240, height: 240 },
  'research-panel': { width: 320, height: 400 },
  'strategy-card': { width: 300, height: 280 },
  'asset-collection': { width: 400, height: 320 },
  'default': DEFAULT_ARTIFACT_SIZE
}