'use client'

import { useState, DragEvent, ClipboardEvent } from 'react'
import { useStudioStore } from '@/state/store'
import {
  calculateNextPosition,
  ARTIFACT_SIZES,
  type Point
} from '@/utils/smartPlacement'

/**
 * Canvas Drop Zone
 * Handles drag-and-drop and paste operations for:
 * - Images (jpg, png, gif, webp, svg)
 * - Documents (pdf, doc, docx)
 * - Links (URLs from clipboard)
 *
 * Auto-creates appropriate cards with intelligent placement
 */

interface CanvasDropZoneProps {
  children: React.ReactNode
}

export function CanvasDropZone({ children }: CanvasDropZoneProps) {
  const [isDragging, setIsDragging] = useState(false)
  const {
    addArtifact,
    canvasArtifacts,
    placement,
    updateLastPosition
  } = useStudioStore()

  /**
   * Calculate next available position for artifact using smart placement
   * @param dropPoint - Optional point where user dropped/clicked
   * @param artifactType - Type of artifact being placed
   */
  const getNextPosition = (
    dropPoint?: Point,
    artifactType: keyof typeof ARTIFACT_SIZES = 'default'
  ): Point => {
    // Define virtual canvas bounds
    const canvasBounds = {
      x: 0,
      y: 0,
      width: 2000,  // Virtual canvas size
      height: 2000,
    }

    // Get existing artifacts with their positions and sizes
    const existingArtifacts = canvasArtifacts
      .filter(a => a.visible)
      .map(a => ({
        position: a.position,
        size: ARTIFACT_SIZES[a.type] || ARTIFACT_SIZES.default
      }))

    // Calculate position using smart placement
    const position = calculateNextPosition({
      strategy: dropPoint ? 'proximity' : placement.strategy,
      canvasBounds,
      existingArtifacts,
      targetPoint: dropPoint,
      artifactSize: ARTIFACT_SIZES[artifactType],
      gridSize: placement.gridSize
    })

    // Update last position in store for future reference
    updateLastPosition(position)

    return position
  }

  /**
   * Handle image file drop - Now with AI processing
   */
  const handleImageFile = async (file: File, dropPoint?: Point) => {
    // Create object URL for preview
    const imageUrl = URL.createObjectURL(file)

    // Create link card artifact with image using smart placement
    const position = getNextPosition(dropPoint, 'link-card')

    console.log('📸 Adding image to canvas:', file.name)
    console.log('Position:', position)
    console.log('File type:', file.type)
    console.log('File size:', file.size)

    // Convert file to base64 for API
    const reader = new FileReader()
    reader.onload = async () => {
      console.log('📸 FileReader loaded, converting to base64...')
      const base64Data = reader.result?.toString().split(',')[1]

      if (!base64Data) {
        console.error('❌ Failed to convert file to base64')
        return
      }

      console.log('✅ Base64 data ready, length:', base64Data.length)

      // Create initial artifact with "processing" state
      const artifactId = Date.now().toString()
      addArtifact({
        type: 'link-card',
        position,
        data: {
          title: file.name,
          description: 'Processing with AI...',
          image: imageUrl,
          url: imageUrl,
          metadata: {
            id: artifactId,
            processing: true,
          }
        },
        visible: true,
      })

      try {
        console.log('📤 Calling /api/discovery/process...')
        // Call processing API
        const response = await fetch('/api/discovery/process', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            contentType: 'image',
            fileName: file.name,
            mimeType: file.type,
            fileData: base64Data,
          }),
        })

        console.log('📥 API Response status:', response.status)
        const result = await response.json()
        console.log('📥 API Response:', result)

        if (result.success && result.result) {
          // Update artifact with AI analysis
          const updatedDescription = result.result.analysis
            ? result.result.analysis.substring(0, 200) + '...'
            : `Image: ${(file.size / 1024).toFixed(1)}KB`

          // Find and update the artifact
          const artifacts = useStudioStore.getState().canvasArtifacts
          const artifact = artifacts.find(a => a.data.metadata?.id === artifactId)

          if (artifact) {
            useStudioStore.getState().updateArtifact(artifact.id, {
              data: {
                ...artifact.data,
                description: updatedDescription,
                metadata: {
                  ...artifact.data.metadata,
                  processing: false,
                  analysis: result.result.analysis,
                  insights: result.result.insights,
                  designElements: result.result.design_elements,
                }
              }
            })
          }
        }
      } catch (error) {
        console.error('Error processing image:', error)
        // Update to show error state
        const artifacts = useStudioStore.getState().canvasArtifacts
        const artifact = artifacts.find(a => a.data.metadata?.id === artifactId)

        if (artifact) {
          useStudioStore.getState().updateArtifact(artifact.id, {
            data: {
              ...artifact.data,
              description: 'Processing failed',
              metadata: {
                ...artifact.data.metadata,
                processing: false,
                error: error instanceof Error ? error.message : 'Unknown error',
              }
            }
          })
        }
      }
    }

    reader.readAsDataURL(file)
  }

  /**
   * Handle document file drop
   */
  const handleDocumentFile = async (file: File, dropPoint?: Point) => {
    const position = getNextPosition(dropPoint, 'sticky-note')

    // Create sticky note with document info
    addArtifact({
      type: 'sticky-note',
      position,
      data: {
        note: `Document: ${file.name}\nSize: ${(file.size / 1024).toFixed(1)}KB\nType: ${file.type}`,
        color: '#F5E6D3', // Warm beige for documents
      },
      visible: true,
    })
  }

  /**
   * Handle URL from clipboard or drag - Now with AI processing
   */
  const handleUrl = async (url: string, dropPoint?: Point) => {
    const position = getNextPosition(dropPoint, 'link-card')

    const artifactId = Date.now().toString()

    // Create link card with processing state
    addArtifact({
      type: 'link-card',
      position,
      data: {
        url,
        title: new URL(url).hostname,
        description: 'Fetching and analyzing...',
        metadata: {
          id: artifactId,
          processing: true,
        }
      },
      visible: true,
    })

    try {
      // Call processing API
      const response = await fetch('/api/discovery/process', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          contentType: 'url',
          fileName: url,
          mimeType: 'text/html',
          url,
        }),
      })

      const result = await response.json()

      if (result.success && result.result) {
        // Update artifact with AI analysis
        const updatedDescription = result.result.analysis
          ? result.result.analysis.substring(0, 200) + '...'
          : 'Analyzed content'

        const artifacts = useStudioStore.getState().canvasArtifacts
        const artifact = artifacts.find(a => a.data.metadata?.id === artifactId)

        if (artifact) {
          useStudioStore.getState().updateArtifact(artifact.id, {
            data: {
              ...artifact.data,
              description: updatedDescription,
              metadata: {
                ...artifact.data.metadata,
                processing: false,
                analysis: result.result.analysis,
                insights: result.result.insights,
                designElements: result.result.design_elements,
              }
            }
          })
        }
      }
    } catch (error) {
      console.error('Error processing URL:', error)

      const artifacts = useStudioStore.getState().canvasArtifacts
      const artifact = artifacts.find(a => a.data.metadata?.id === artifactId)

      if (artifact) {
        useStudioStore.getState().updateArtifact(artifact.id, {
          data: {
            ...artifact.data,
            description: 'Processing failed',
            metadata: {
              ...artifact.data.metadata,
              processing: false,
              error: error instanceof Error ? error.message : 'Unknown error',
            }
          }
        })
      }
    }
  }

  /**
   * Drag over handler - show drop indicator
   */
  const handleDragOver = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()

    // Show drop indicator
    if (!isDragging) {
      setIsDragging(true)
    }
  }

  /**
   * Drag leave handler - hide drop indicator
   */
  const handleDragLeave = (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()

    // Only hide if leaving the canvas entirely
    if (e.currentTarget === e.target) {
      setIsDragging(false)
    }
  }

  /**
   * Drop handler - process dropped items with proximity placement
   */
  const handleDrop = async (e: DragEvent<HTMLDivElement>) => {
    e.preventDefault()
    e.stopPropagation()
    setIsDragging(false)

    const { files, items } = e.dataTransfer

    // Get drop point relative to the canvas
    const rect = e.currentTarget.getBoundingClientRect()
    const dropPoint: Point = {
      x: e.clientX - rect.left,
      y: e.clientY - rect.top
    }

    // Handle file drops
    if (files.length > 0) {
      const filePromises = Array.from(files).map(async (file, index) => {
        // Offset each subsequent file slightly to avoid stacking
        const offsetPoint = index > 0 ? {
          x: dropPoint.x + (index * 40),
          y: dropPoint.y + (index * 40)
        } : dropPoint

        // Check if it's an image
        if (file.type.startsWith('image/')) {
          await handleImageFile(file, offsetPoint)
        }
        // Check if it's a document
        else if (
          file.type.includes('pdf') ||
          file.type.includes('document') ||
          file.type.includes('msword') ||
          file.type.includes('officedocument')
        ) {
          handleDocumentFile(file, offsetPoint)
        }
      })

      // Wait for all file processing to complete
      await Promise.all(filePromises)
    }

    // Handle URL drops (e.g., dragged from browser)
    if (items.length > 0) {
      Array.from(items).forEach((item) => {
        if (item.kind === 'string' && item.type === 'text/uri-list') {
          item.getAsString((url) => {
            if (url.startsWith('http://') || url.startsWith('https://')) {
              handleUrl(url, dropPoint)
            }
          })
        }
      })
    }
  }

  /**
   * Paste handler - handle pasted URLs (uses spiral placement)
   */
  const handlePaste = async (e: ClipboardEvent<HTMLDivElement>) => {
    const text = e.clipboardData.getData('text')

    // Check if it's a valid URL
    if (text && (text.startsWith('http://') || text.startsWith('https://'))) {
      e.preventDefault()
      // No drop point for paste, so it will use the default strategy (spiral)
      handleUrl(text)
    }
  }

  return (
    <div
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onPaste={handlePaste}
      tabIndex={0} // Make focusable for paste events
      style={{
        position: 'relative',
        width: '100%',
        height: '100%',
        outline: 'none',
      }}
    >
      {children}

      {/* Drop Indicator Overlay */}
      {isDragging && (
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'var(--color-primary-subtle)',
            border: '2px dashed var(--primary)',
            borderRadius: '8px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            pointerEvents: 'none',
            zIndex: 50,
          }}
        >
          <div
            style={{
              background: 'white',
              padding: '24px 48px',
              borderRadius: '12px',
              boxShadow: 'var(--shadow-panel)',
              textAlign: 'center',
            }}
          >
            <p
              style={{
                fontSize: '18px',
                fontWeight: 600,
                marginBottom: '8px',
              }}
            >
              Drop to add to canvas
            </p>
            <p
              style={{
                fontSize: '14px',
                color: 'var(--text-muted)',
              }}
            >
              Images, documents, and links supported
            </p>
          </div>
        </div>
      )}
    </div>
  )
}
