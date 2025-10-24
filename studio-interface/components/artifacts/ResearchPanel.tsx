'use client'

import { useEffect, useState } from 'react'
import { useDraggable } from '@amplified/interactions'
import { useStudioStore, type CanvasArtifact } from '@/state/store'

interface ResearchPanelProps {
  artifact: CanvasArtifact
  onUpdate?: (updates: Partial<CanvasArtifact>) => void
}

/**
 * Research Panel - Entity information with images and articles
 * Auto-searches for entity info
 * Draggable and repositionable
 */
export function ResearchPanel({ artifact, onUpdate }: ResearchPanelProps) {
  const { entity, bio, images, articles, loading } = artifact.data
  const [expanded, setExpanded] = useState(false)
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

  useEffect(() => {
    // Fetch entity info if still loading
    if (loading && entity) {
      searchEntity(entity).then((info) => {
        onUpdate?.({
          data: {
            ...artifact.data,
            ...info,
            loading: false,
          },
        })
      })
    }
  }, [loading, entity, artifact.data, onUpdate])

  return (
    <div
      ref={ref}
      className="studio-panel artifact-entering"
      onClick={handleClick}
      style={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        width: expanded ? '400px' : '320px',
        borderRadius: '12px',
        border: isSelected ? '2px solid var(--color-selection)' : '1px solid var(--border)',
        cursor: isDragging ? 'grabbing' : 'grab',
        transition: isDragging ? 'none' : 'width 200ms, box-shadow 200ms, border 150ms',
        boxShadow: isDragging ? 'var(--shadow-modal)' : isSelected ? '0 8px 24px var(--color-selection-subtle)' : 'var(--shadow-panel)',
        zIndex: isDragging ? 1000 : isSelected ? 100 : 1,
        animationDelay: `${entranceDelay}ms`,
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '16px',
          borderBottom: '1px solid rgba(218, 221, 216, 0.4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <div>
          <span
            style={{
              fontSize: '11px',
              color: 'var(--text-muted)',
              textTransform: 'uppercase',
              letterSpacing: '0.05em',
              fontWeight: 500,
              display: 'block',
              marginBottom: '4px',
            }}
          >
            Research
          </span>
          <h3
            className="font-heading"
            style={{
              fontSize: '16px',
              fontWeight: 600,
              lineHeight: '1.3',
            }}
          >
            {entity}
          </h3>
        </div>
        <button
          className="studio-button studio-button-sm studio-button-ghost"
          onClick={() => setExpanded(!expanded)}
          style={{ padding: '4px 8px' }}
        >
          {expanded ? '−' : '+'}
        </button>
      </div>

      {/* Content */}
      <div style={{ padding: '16px' }}>
        {loading ? (
          <div>
            <div
              className="skeleton-text"
              style={{ width: '100%', height: '60px', marginBottom: '12px' }}
            />
            <div className="skeleton-text" style={{ width: '60%', height: '20px' }} />
          </div>
        ) : (
          <>
            {/* Bio */}
            {bio && (
              <p
                style={{
                  fontSize: '14px',
                  lineHeight: '1.6',
                  color: 'var(--text)',
                  marginBottom: '16px',
                }}
              >
                {bio}
              </p>
            )}

            {/* Images */}
            {images && images.length > 0 && (
              <div style={{ marginBottom: '16px' }}>
                <h4
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    marginBottom: '8px',
                    color: 'var(--text-muted)',
                  }}
                >
                  Images ({images.length})
                </h4>
                <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(80px, 1fr))',
                    gap: '8px',
                  }}
                >
                  {images.slice(0, expanded ? images.length : 4).map((img, i) => (
                    <div
                      key={i}
                      style={{
                        aspectRatio: '1',
                        borderRadius: '6px',
                        overflow: 'hidden',
                        background: 'var(--surface-muted)',
                      }}
                    >
                      <img
                        src={img}
                        alt=""
                        style={{
                          width: '100%',
                          height: '100%',
                          objectFit: 'cover',
                        }}
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Articles */}
            {articles && articles.length > 0 && expanded && (
              <div>
                <h4
                  style={{
                    fontSize: '12px',
                    fontWeight: 600,
                    marginBottom: '8px',
                    color: 'var(--text-muted)',
                  }}
                >
                  Articles
                </h4>
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {articles.map((article, i) => (
                    <a
                      key={i}
                      href={article.url}
                      target="_blank"
                      rel="noopener noreferrer"
                      className="studio-button studio-button-sm studio-button-ghost"
                      style={{
                        justifyContent: 'flex-start',
                        textAlign: 'left',
                        fontSize: '13px',
                      }}
                    >
                      {article.title}
                    </a>
                  ))}
                </div>
              </div>
            )}

            {/* Empty state */}
            {!bio && (!images || images.length === 0) && (!articles || articles.length === 0) && (
              <p style={{ fontSize: '14px', color: 'var(--text-muted)', textAlign: 'center' }}>
                No information found
              </p>
            )}
          </>
        )}
      </div>
    </div>
  )
}

/**
 * Search for entity information
 * TODO: Implement actual API call
 */
async function searchEntity(entity: string): Promise<{
  bio: string
  images: string[]
  articles: Array<{ title: string; url: string }>
}> {
  try {
    // Mock implementation - replace with actual API
    // Options: Wikipedia API, Google Custom Search, etc.

    return {
      bio: `${entity} is a notable figure. More information will be gathered from various sources.`,
      images: [],
      articles: [
        {
          title: `About ${entity}`,
          url: `https://en.wikipedia.org/wiki/${encodeURIComponent(entity)}`,
        },
      ],
    }
  } catch (error) {
    return {
      bio: '',
      images: [],
      articles: [],
    }
  }
}
