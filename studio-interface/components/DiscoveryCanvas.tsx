'use client'

import { useEffect, useRef, useCallback, useState } from 'react'
import { useStudioStore } from '@/state/store'
import { useCanvasTransform } from '@/hooks/useCanvasTransform'
import { SparkleIcon } from '@/components/icons/Icon'
import { LinkCard } from './artifacts/LinkCard'
import { ResearchPanel } from './artifacts/ResearchPanel'
import { StickyNote } from './artifacts/StickyNote'
import { StrategyCard } from './artifacts/StrategyCard'
import { CanvasDropZone } from './CanvasDropZone'
import { SelectionProvider } from './canvas/SelectionContext'
import { SelectionToolbar } from './canvas/SelectionToolbar'
import { MarqueeBox } from './canvas/MarqueeBox'
import { DeleteConfirmModal } from './canvas/DeleteConfirmModal'

/**
 * Discovery Canvas - Builds progressively as conversation progresses
 * Shows visual artifacts: links, research, notes, strategies
 * Supports drag-and-drop for images, documents, and links
 * Supports pan and zoom with keyboard, mouse, and trackpad
 */
export function DiscoveryCanvas() {
  const {
    canvasArtifacts,
    updateArtifact,
    clearSelection,
    selectAll,
    selectArtifact,
    selection,
    setMarqueeStart,
    setMarqueeEnd,
    clearMarquee,
    getMarqueeIntersections,
    marquee,
    showDeleteConfirmation,
    deleteArtifacts
  } = useStudioStore()
  const canvasRef = useRef<HTMLDivElement>(null)
  const contentRef = useRef<HTMLDivElement>(null)
  const [isMarqueeing, setIsMarqueeing] = useState(false)

  const { transform, isPanning, handlers } = useCanvasTransform({
    minScale: 0.25,
    maxScale: 3,
    initialScale: 1,
  })

  // Filter visible artifacts
  const visibleArtifacts = canvasArtifacts.filter((a) => a.visible)

  // Handle canvas click to clear selection
  const handleCanvasClick = useCallback((e: React.MouseEvent) => {
    // Only clear if clicking directly on canvas (not artifacts)
    if (e.currentTarget === e.target || e.target === contentRef.current) {
      clearSelection()
    }
  }, [clearSelection])

  // Handle mouse down for marquee start
  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    // Only start marquee if clicking on empty canvas (not artifacts)
    if (e.target !== canvasRef.current && e.target !== contentRef.current) {
      return
    }

    // Don't interfere with pan (middle mouse or space+drag)
    if (e.button !== 0) return

    const rect = contentRef.current?.getBoundingClientRect()
    if (!rect) return

    const point = {
      x: (e.clientX - rect.left - transform.x) / transform.scale,
      y: (e.clientY - rect.top - transform.y) / transform.scale
    }

    setIsMarqueeing(true)
    setMarqueeStart(point, {
      shift: e.shiftKey,
      alt: e.altKey
    })
  }, [setMarqueeStart, transform])

  // Handle mouse move for marquee update
  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isMarqueeing) return

    const rect = contentRef.current?.getBoundingClientRect()
    if (!rect) return

    const point = {
      x: (e.clientX - rect.left - transform.x) / transform.scale,
      y: (e.clientY - rect.top - transform.y) / transform.scale
    }

    setMarqueeEnd(point)
  }, [isMarqueeing, setMarqueeEnd, transform])

  // Handle mouse up for marquee complete
  const handleMouseUp = useCallback(() => {
    if (!isMarqueeing) return

    // Get intersecting artifacts
    const intersections = getMarqueeIntersections()

    if (marquee.modifiers.shift) {
      // Add to selection
      intersections.forEach(id => selectArtifact(id, { cmd: true }))
    } else if (marquee.modifiers.alt) {
      // Subtract from selection (toggle off)
      intersections.forEach(id => {
        if (selection.ids.has(id)) {
          selectArtifact(id, { cmd: true })
        }
      })
    } else {
      // Replace selection
      if (intersections.length > 0) {
        clearSelection()
        intersections.forEach(id => selectArtifact(id, { cmd: true }))
      }
    }

    setIsMarqueeing(false)
    clearMarquee()
  }, [isMarqueeing, getMarqueeIntersections, marquee.modifiers, selectArtifact, clearSelection, clearMarquee, selection.ids])

  // Handle keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Cmd/Ctrl + A to select all
    if ((e.metaKey || e.ctrlKey) && e.key === 'a') {
      e.preventDefault()
      selectAll()
    }

    // Escape to clear selection
    if (e.key === 'Escape') {
      clearSelection()
    }

    // Delete/Backspace to delete selected items
    if (e.key === 'Delete' || e.key === 'Backspace') {
      const selectedIds = Array.from(selection.ids)

      if (selectedIds.length > 0) {
        e.preventDefault()

        // Show confirmation if >3 items
        if (selectedIds.length > 3) {
          showDeleteConfirmation(selectedIds)
        } else {
          deleteArtifacts(selectedIds)
        }
      }
    }

    // Pass through to canvas transform handler
    handlers.onKeyDown(e)
  }, [selectAll, clearSelection, selection.ids, showDeleteConfirmation, deleteArtifacts, handlers])

  // Attach event listeners
  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return

    canvas.addEventListener('wheel', handlers.onWheel, { passive: false })
    canvas.addEventListener('mousedown', handlers.onMouseDown)
    window.addEventListener('mousemove', handlers.onMouseMove)
    window.addEventListener('mouseup', handlers.onMouseUp)
    window.addEventListener('keydown', handleKeyDown)

    return () => {
      canvas.removeEventListener('wheel', handlers.onWheel)
      canvas.removeEventListener('mousedown', handlers.onMouseDown)
      window.removeEventListener('mousemove', handlers.onMouseMove)
      window.removeEventListener('mouseup', handlers.onMouseUp)
      window.removeEventListener('keydown', handleKeyDown)
    }
  }, [handlers, handleKeyDown])

  // Marquee event listeners
  useEffect(() => {
    if (isMarqueeing) {
      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)

      return () => {
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }
    }
  }, [isMarqueeing, handleMouseMove, handleMouseUp])

  return (
    <SelectionProvider>
      {/* Delete confirmation modal */}
      <DeleteConfirmModal />

      <CanvasDropZone>
        <div
          ref={canvasRef}
          onClick={handleCanvasClick}
          onMouseDown={handleMouseDown}
          style={{
            flex: 1,
            position: 'relative',
            background: 'var(--canvas-bg, var(--background))',
            overflow: 'hidden',
            minHeight: '100%',
            cursor: isPanning ? 'grabbing' : 'default',
          }}
        >
          {/* Selection Toolbar - appears when items are selected */}
          {selection.ids.size > 0 && <SelectionToolbar />}

          {/* Transformable content layer */}
          <div
            ref={contentRef}
            style={{
            position: 'absolute',
            inset: 0,
            transform: `translate(${transform.x}px, ${transform.y}px) scale(${transform.scale})`,
            transformOrigin: '0 0',
            transition: isPanning ? 'none' : 'transform 0.1s ease-out',
          }}
        >
          {/* Grid overlay (moves with canvas) */}
          <div
            style={{
              position: 'absolute',
              inset: '-200%',
              width: '500%',
              height: '500%',
              backgroundImage: `
                linear-gradient(rgba(218, 221, 216, 0.1) 1px, transparent 1px),
                linear-gradient(90deg, rgba(218, 221, 216, 0.1) 1px, transparent 1px)
              `,
              backgroundSize: '40px 40px',
              pointerEvents: 'none',
              opacity: 0.5,
            }}
          />

          {/* Empty State */}
          {visibleArtifacts.length === 0 && (
          <div
            style={{
              position: 'absolute',
              top: '50%',
              left: '50%',
              transform: 'translate(-50%, -50%)',
              textAlign: 'center',
              maxWidth: '400px',
            }}
          >
            <div
              style={{
                width: '120px',
                height: '120px',
                margin: '0 auto 24px',
                borderRadius: '50%',
                background: 'var(--color-primary-subtle)',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
            >
              <SparkleIcon size={48} strokeWidth={1.5} />
            </div>
            <h2
              className="font-heading"
              style={{
                fontSize: '24px',
                fontWeight: 600,
                marginBottom: '12px',
              }}
            >
              Let&rsquo;s get started
            </h2>
            <p
              style={{
                fontSize: '15px',
                lineHeight: '1.6',
                color: 'var(--text-muted)',
              }}
            >
              Share your ideas through chat, or drag and drop images, documents, and links directly onto the canvas.
            </p>
          </div>
          )}

          {/* Artifacts */}
          {visibleArtifacts.map((artifact) => {
            const componentProps = {
              artifact,
              onUpdate: (updates: Partial<typeof artifact>) =>
                updateArtifact(artifact.id, updates),
            }

            switch (artifact.type) {
              case 'link-card':
                return <LinkCard key={artifact.id} {...componentProps} />
              case 'research-panel':
                return <ResearchPanel key={artifact.id} {...componentProps} />
              case 'sticky-note':
                return <StickyNote key={artifact.id} {...componentProps} />
              case 'strategy-card':
                return <StrategyCard key={artifact.id} {...componentProps} />
              default:
                return null
            }
          })}

          {/* Marquee selection box */}
          {marquee.active && <MarqueeBox />}
        </div>

        {/* Zoom indicator */}
        {transform.scale !== 1 && (
          <div
            style={{
              position: 'absolute',
              bottom: '16px',
              right: '16px',
              padding: '8px 12px',
              background: 'var(--bg-primary)',
              border: '1px solid var(--border)',
              borderRadius: '8px',
              fontSize: '13px',
              fontWeight: 500,
              color: 'var(--text-muted)',
              pointerEvents: 'none',
              boxShadow: '0 2px 8px rgba(0, 0, 0, 0.08)',
            }}
          >
            {Math.round(transform.scale * 100)}%
          </div>
        )}
      </div>
      </CanvasDropZone>
    </SelectionProvider>
  )
}
