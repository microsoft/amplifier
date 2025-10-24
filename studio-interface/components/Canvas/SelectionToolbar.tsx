'use client'

import React, { useEffect, useState, useMemo } from 'react'
import { useStudioStore } from '@/state/store'
import { TrashIcon } from '@/components/icons/Icon'

/**
 * SelectionToolbar - Appears when items are selected
 * Shows count of selected items and actions
 * Positioned above the selection bounding box
 */
export function SelectionToolbar() {
  const selection = useStudioStore((state) => state.selection)
  const canvasArtifacts = useStudioStore((state) => state.canvasArtifacts)
  const showDeleteConfirmation = useStudioStore((state) => state.showDeleteConfirmation)
  const deleteArtifacts = useStudioStore((state) => state.deleteArtifacts)

  // Memoize selected artifacts to prevent infinite re-renders
  const selectedArtifacts = useMemo(() => {
    return canvasArtifacts.filter(artifact => selection.ids.has(artifact.id))
  }, [canvasArtifacts, selection.ids])

  const count = selectedArtifacts.length

  const [isVisible, setIsVisible] = useState(false)
  const [boundingBox, setBoundingBox] = useState({ top: 0, left: 0, width: 0, height: 0 })

  // Calculate bounding box of selected items
  useEffect(() => {
    if (count === 0) {
      setIsVisible(false)
      return
    }

    // Calculate the bounding box from artifact positions
    let minX = Infinity
    let minY = Infinity
    let maxX = -Infinity
    let maxY = -Infinity

    selectedArtifacts.forEach((artifact) => {
      const x = artifact.position.x
      const y = artifact.position.y
      // Approximate dimensions - will be refined later
      const width = 280  // LinkCard default width
      const height = 200 // Approximate height

      minX = Math.min(minX, x)
      minY = Math.min(minY, y)
      maxX = Math.max(maxX, x + width)
      maxY = Math.max(maxY, y + height)
    })

    setBoundingBox({
      left: minX + (maxX - minX) / 2,
      top: minY - 60, // Position above the selection
      width: maxX - minX,
      height: maxY - minY,
    })

    // Animate in after a brief delay
    requestAnimationFrame(() => {
      setIsVisible(true)
    })
  }, [count, selectedArtifacts])

  if (count === 0) return null

  const handleDelete = () => {
    const ids = Array.from(selection.ids)

    // Show confirmation if >3 items
    if (ids.length > 3) {
      showDeleteConfirmation(ids)
    } else {
      // Direct delete for ≤3 items
      deleteArtifacts(ids)
    }
  }

  return (
    <div
      className="selection-toolbar"
      style={{
        position: 'absolute',
        left: `${boundingBox.left}px`,
        top: `${boundingBox.top}px`,
        transform: 'translateX(-50%)',
        display: 'flex',
        alignItems: 'center',
        gap: '8px',
        padding: '8px 16px',
        background: 'white',
        borderRadius: '12px',
        boxShadow: '0 4px 12px rgba(0, 0, 0, 0.15)',
        border: '1px solid var(--border)',
        zIndex: 2000,
        opacity: isVisible ? 1 : 0,
        scale: isVisible ? 1 : 0.9,
        transition: 'opacity 200ms cubic-bezier(0.4, 0, 0.2, 1), scale 200ms cubic-bezier(0.4, 0, 0.2, 1)',
        pointerEvents: isVisible ? 'all' : 'none',
      }}
    >
      {/* Selection count */}
      <span
        style={{
          fontSize: '14px',
          fontWeight: 500,
          color: 'var(--text-primary)',
        }}
      >
        {count} selected
      </span>

      {/* Delete button */}
      <button
        onClick={handleDelete}
        title="Delete (⌫)"
        style={{
          width: '32px',
          height: '32px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '8px',
          background: 'transparent',
          border: 'none',
          color: 'var(--text-primary)',
          cursor: 'pointer',
          transition: 'background 150ms, color 150ms',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.background = 'var(--error-bg, #FEE2E2)'
          e.currentTarget.style.color = 'var(--error, #E53E3E)'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.background = 'transparent'
          e.currentTarget.style.color = 'var(--text-primary)'
        }}
      >
        <TrashIcon size={18} />
      </button>
    </div>
  )
}