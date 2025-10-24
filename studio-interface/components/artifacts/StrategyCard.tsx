'use client'

import { useDraggable } from '@amplified/interactions'
import { useStudioStore, type CanvasArtifact } from '@/state/store'

interface StrategyCardProps {
  artifact: CanvasArtifact
  onUpdate?: (updates: Partial<CanvasArtifact>) => void
}

/**
 * Strategy Card - Goals and channels
 * Represents distribution channels or strategic goals
 * Draggable and repositionable
 */
export function StrategyCard({ artifact, onUpdate }: StrategyCardProps) {
  const { strategy, channel, goals } = artifact.data
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
      className="studio-panel artifact-entering"
      onClick={handleClick}
      style={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        width: '280px',
        borderRadius: '12px',
        cursor: isDragging ? 'grabbing' : 'grab',
        background: 'var(--color-accent-subtle)',
        border: isSelected ? '2px solid var(--color-selection)' : '1px solid var(--color-primary-border)',
        boxShadow: isDragging ? 'var(--shadow-modal)' : isSelected ? '0 8px 24px var(--color-selection-subtle)' : 'var(--shadow-panel)',
        transition: isDragging ? 'none' : 'box-shadow 200ms, border 150ms',
        zIndex: isDragging ? 1000 : isSelected ? 100 : 1,
        animationDelay: `${entranceDelay}ms`,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid var(--color-primary-border-subtle)',
        }}
      >
        <span
          style={{
            fontSize: '11px',
            color: 'var(--primary)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            fontWeight: 500,
            display: 'block',
            marginBottom: '6px',
          }}
        >
          Strategy
        </span>
        <h3
          className="font-heading"
          style={{
            fontSize: '18px',
            fontWeight: 600,
            lineHeight: '1.3',
          }}
        >
          {strategy || channel}
        </h3>
      </div>

      {/* Goals */}
      <div style={{ padding: '16px' }}>
        {goals && goals.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <span
              style={{
                fontSize: '11px',
                color: 'var(--text-muted)',
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                fontWeight: 500,
              }}
            >
              Goals
            </span>
            {goals.map((goal, i) => (
              <div
                key={i}
                style={{
                  fontSize: '14px',
                  padding: '8px 12px',
                  background: 'rgba(255, 255, 255, 0.5)',
                  borderRadius: '6px',
                  lineHeight: '1.4',
                }}
              >
                {goal}
              </div>
            ))}
          </div>
        ) : (
          <p
            style={{
              fontSize: '14px',
              color: 'var(--text-muted)',
              lineHeight: '1.6',
            }}
          >
            Strategy identified - goals will be refined through conversation
          </p>
        )}
      </div>
    </div>
  )
}
