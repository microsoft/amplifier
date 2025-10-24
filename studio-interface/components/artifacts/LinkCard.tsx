'use client'

import { useEffect, useState } from 'react'
import { useDraggable } from '@amplified/interactions'
import { useStudioStore, type CanvasArtifact } from '@/state/store'
import { ResizeHandles } from '../canvas/ResizeHandles'

interface LinkCardProps {
  artifact: CanvasArtifact
  onUpdate?: (updates: Partial<CanvasArtifact>) => void
}

/**
 * Link Card - URL preview with metadata
 * Auto-fetches title, description, image
 * Draggable and repositionable
 */
export function LinkCard({ artifact, onUpdate }: LinkCardProps) {
  const { url, title, description, image, favicon, loading } = artifact.data
  const [imageError, setImageError] = useState(false)
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

  useEffect(() => {
    // Fetch metadata if still loading
    if (loading && url) {
      fetchMetadata(url).then((metadata) => {
        onUpdate?.({
          data: {
            ...artifact.data,
            ...metadata,
            loading: false,
          },
        })
      })
    }
  }, [loading, url, artifact.data, onUpdate])

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
        width: '280px',
        borderRadius: '16px',
        overflow: 'visible', // Changed to show resize handles
        cursor: isDragging ? 'grabbing' : 'grab',
        background: 'var(--bg-primary)',
        border: isSelected ? '2px solid var(--color-selection)' : '1px solid var(--border)',
        boxShadow: isDragging ? '0 12px 40px rgba(0, 0, 0, 0.15)' : isSelected ? '0 8px 24px var(--color-selection-subtle)' : '0 4px 12px rgba(0, 0, 0, 0.08)',
        transition: isDragging ? 'none' : 'box-shadow 150ms, border 150ms',
        zIndex: isDragging ? 1000 : isSelected ? 100 : 1,
        animationDelay: `${entranceDelay}ms`,
      }}
    >
      {/* Image */}
      {image && !imageError ? (
        <div>
          <div style={{ position: 'relative', borderRadius: '16px 16px 0 0', overflow: 'hidden' }}>
            <img
              src={image}
              alt={title || 'Image preview'}
              onError={() => setImageError(true)}
              style={{
                width: '100%',
                height: 'auto',
                display: 'block',
              }}
            />
          </div>

          {/* Caption bar */}
          {(title || description) && (
            <div
              title={description || title} // Tooltip on hover
              style={{
                padding: '8px 12px',
                background: 'var(--bg-secondary)',
                borderTop: '1px solid var(--border)',
              }}
            >
              <p
                style={{
                  fontSize: '13px',
                  fontWeight: 500,
                  color: 'var(--text-primary)',
                  margin: 0,
                  overflow: 'hidden',
                  textOverflow: 'ellipsis',
                  whiteSpace: 'nowrap',
                }}
              >
                {title || new URL(url).hostname}
              </p>
            </div>
          )}
        </div>
      ) : (
        // Fallback for no image
        <div
          style={{
            padding: '24px',
            display: 'flex',
            flexDirection: 'column',
            gap: '8px',
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            {favicon && (
              <img
                src={favicon}
                alt=""
                style={{ width: '16px', height: '16px' }}
                onError={(e) => (e.currentTarget.style.display = 'none')}
              />
            )}
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              {url ? new URL(url).hostname : ''}
            </span>
          </div>

          <h3
            style={{
              fontSize: '15px',
              fontWeight: 500,
              lineHeight: '1.4',
              color: 'var(--text-primary)',
            }}
          >
            {loading ? 'Loading...' : title || url}
          </h3>
        </div>
      )}

      {/* Resize handles - only when selected */}
      <ResizeHandles
        isSelected={isSelected && !isDragging}
        onResize={(dimensions) => {
          // Handle resize - for now just a placeholder, will implement sizing later
          // eslint-disable-next-line @typescript-eslint/no-unused-vars
          const _ = dimensions
        }}
        currentWidth={280}
        currentHeight={200}
      />

      {/* Selection toolbar - appears below when selected */}
      {isSelected && !isDragging && (
        <div
          style={{
            position: 'absolute',
            bottom: '-48px',
            left: '50%',
            transform: 'translateX(-50%)',
            display: 'flex',
            gap: '4px',
            padding: '8px',
            background: 'white',
            borderRadius: '12px',
            boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
            border: '1px solid var(--border)',
            zIndex: 1000,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {/* Open Link button */}
          <a
            href={url}
            target="_blank"
            rel="noopener noreferrer"
            title="Open Link"
            style={{
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '8px',
              background: 'transparent',
              color: 'var(--text-primary)',
              textDecoration: 'none',
              transition: 'background 150ms',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-secondary)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6" />
              <polyline points="15 3 21 3 21 9" />
              <line x1="10" y1="14" x2="21" y2="3" />
            </svg>
          </a>

          {/* Crop/Edit button */}
          <button
            title="Crop"
            style={{
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '8px',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              transition: 'background 150ms',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-secondary)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M6.13 1L6 16a2 2 0 0 0 2 2h15" />
              <path d="M1 6.13L16 6a2 2 0 0 1 2 2v15" />
            </svg>
          </button>

          {/* View/Preview button */}
          <button
            title="View Full Size"
            style={{
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: '8px',
              background: 'transparent',
              border: 'none',
              color: 'var(--text-primary)',
              cursor: 'pointer',
              transition: 'background 150ms',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-secondary)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
          >
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z" />
              <circle cx="12" cy="12" r="3" />
            </svg>
          </button>
        </div>
      )}
    </div>
  )
}

/**
 * Fetch metadata for URL
 * TODO: Implement actual API call
 */
async function fetchMetadata(url: string): Promise<{
  title: string
  description: string
  image: string
  favicon: string
}> {
  try {
    // Mock implementation - replace with actual API
    const domain = new URL(url).hostname

    return {
      title: `Preview: ${domain}`,
      description: 'Link preview will be fetched from metadata',
      image: '',
      favicon: `https://www.google.com/s2/favicons?domain=${domain}&sz=32`,
    }
  } catch (error) {
    return {
      title: url,
      description: '',
      image: '',
      favicon: '',
    }
  }
}
