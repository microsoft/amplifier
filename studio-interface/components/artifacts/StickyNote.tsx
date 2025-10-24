'use client'

import { useDraggable } from '@amplified/interactions'
import { useStudioStore, type CanvasArtifact } from '@/state/store'

interface StickyNoteProps {
  artifact: CanvasArtifact
  onUpdate?: (updates: Partial<CanvasArtifact>) => void
}

/**
 * Sticky Note - Key insights and decisions
 * Captures important statements from conversation
 * Draggable and repositionable
 */
export function StickyNote({ artifact, onUpdate }: StickyNoteProps) {
  const { note, color } = artifact.data
  const isSelected = useStudioStore((state) => state.isSelected(artifact.id))
  const selectArtifact = useStudioStore((state) => state.selectArtifact)
  const getEntranceDelay = useStudioStore((state) => state.getEntranceDelay)

  const { ref, position, isDragging } = useDraggable({
    initialPosition: artifact.position,
    onDragEnd: (newPosition) => {
      onUpdate?.({ position: newPosition })
    },
  })

  // Calculate entrance delay for stagger effect
  const entranceDelay = getEntranceDelay(artifact.id)

  const handleClick = (e: React.MouseEvent) => {
    // Prevent selection when dragging
    if (isDragging) return

    // Stop propagation to prevent canvas click from clearing selection
    e.stopPropagation()

    // Use global selection with modifiers
    selectArtifact(artifact.id, {
      cmd: e.metaKey || e.ctrlKey,
      shift: e.shiftKey
    })
  }

  return (
    <div
      ref={ref}
      className="artifact-entering"
      onClick={handleClick}
      style={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        width: '240px',
        minHeight: '120px',
        padding: '16px',
        background: color || '#FEF3C7',
        borderRadius: '8px',
        border: isSelected ? '2px solid var(--color-selection)' : '1px solid transparent',
        boxShadow: isDragging ? '0 8px 24px rgba(0, 0, 0, 0.2)' : isSelected ? '0 4px 16px var(--color-selection-subtle)' : '0 2px 8px rgba(0, 0, 0, 0.1)',
        cursor: isDragging ? 'grabbing' : 'grab',
        fontFamily: 'var(--font-geist-mono), monospace',
        fontSize: '14px',
        lineHeight: '1.5',
        color: '#1C1C1C',
        transition: isDragging ? 'none' : 'transform 200ms, box-shadow 200ms, border 150ms',
        transform: isDragging ? 'scale(1.02) rotate(0.5deg)' : 'scale(1) rotate(0deg)',
        zIndex: isDragging ? 1000 : isSelected ? 100 : 1,
        animationDelay: `${entranceDelay}ms`,
      }}
    >
      <div
        style={{
          fontSize: '11px',
          opacity: 0.6,
          marginBottom: '8px',
          textTransform: 'uppercase',
          letterSpacing: '0.05em',
        }}
      >
        Note
      </div>
      {note}
    </div>
  )
}
