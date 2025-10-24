'use client'

import { useState, useCallback } from 'react'

interface ResizeHandlesProps {
  isSelected: boolean
  onResize: (dimensions: { width: number; height: number }) => void
  currentWidth: number
  currentHeight: number
}

type ResizeHandle = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w'

/**
 * Resize Handles Component
 * Shows blue corner and edge dots when selected (like inspiration image)
 * Allows resizing canvas artifacts
 */
export function ResizeHandles({ isSelected, onResize, currentWidth, currentHeight }: ResizeHandlesProps) {
  const [activeHandle, setActiveHandle] = useState<ResizeHandle | null>(null)

  const handleMouseDown = useCallback(
    (handle: ResizeHandle, e: React.MouseEvent) => {
      e.stopPropagation()
      e.preventDefault()

      const startX = e.clientX
      const startY = e.clientY
      const startWidth = currentWidth
      const startHeight = currentHeight

      setActiveHandle(handle)

      const handleMouseMove = (moveEvent: MouseEvent) => {
        const deltaX = moveEvent.clientX - startX
        const deltaY = moveEvent.clientY - startY

        let newWidth = startWidth
        let newHeight = startHeight

        // Calculate new dimensions based on handle direction
        switch (handle) {
          case 'e':
          case 'ne':
          case 'se':
            newWidth = Math.max(100, startWidth + deltaX)
            break
          case 'w':
          case 'nw':
          case 'sw':
            newWidth = Math.max(100, startWidth - deltaX)
            break
        }

        switch (handle) {
          case 's':
          case 'se':
          case 'sw':
            newHeight = Math.max(80, startHeight + deltaY)
            break
          case 'n':
          case 'ne':
          case 'nw':
            newHeight = Math.max(80, startHeight - deltaY)
            break
        }

        // Maintain aspect ratio for corner handles if needed
        // (can be made optional with Shift key later)
        if (['nw', 'ne', 'se', 'sw'].includes(handle)) {
          const aspectRatio = startWidth / startHeight
          newHeight = newWidth / aspectRatio
        }

        onResize({ width: newWidth, height: newHeight })
      }

      const handleMouseUp = () => {
        setActiveHandle(null)
        window.removeEventListener('mousemove', handleMouseMove)
        window.removeEventListener('mouseup', handleMouseUp)
      }

      window.addEventListener('mousemove', handleMouseMove)
      window.addEventListener('mouseup', handleMouseUp)
    },
    [currentWidth, currentHeight, onResize]
  )

  if (!isSelected) return null

  const handleStyle = (position: ResizeHandle): React.CSSProperties => {
    const base: React.CSSProperties = {
      position: 'absolute',
      width: '8px',
      height: '8px',
      background: 'var(--color-selection)',
      border: '2px solid white',
      borderRadius: '50%',
      cursor: getCursor(position),
      boxShadow: '0 1px 3px rgba(0, 0, 0, 0.2)',
      zIndex: 10,
    }

    const positions: Record<ResizeHandle, React.CSSProperties> = {
      nw: { top: '-4px', left: '-4px' },
      n: { top: '-4px', left: '50%', transform: 'translateX(-50%)' },
      ne: { top: '-4px', right: '-4px' },
      e: { top: '50%', right: '-4px', transform: 'translateY(-50%)' },
      se: { bottom: '-4px', right: '-4px' },
      s: { bottom: '-4px', left: '50%', transform: 'translateX(-50%)' },
      sw: { bottom: '-4px', left: '-4px' },
      w: { top: '50%', left: '-4px', transform: 'translateY(-50%)' },
    }

    return { ...base, ...positions[position] }
  }

  const getCursor = (position: ResizeHandle): string => {
    const cursors: Record<ResizeHandle, string> = {
      nw: 'nwse-resize',
      n: 'ns-resize',
      ne: 'nesw-resize',
      e: 'ew-resize',
      se: 'nwse-resize',
      s: 'ns-resize',
      sw: 'nesw-resize',
      w: 'ew-resize',
    }
    return cursors[position]
  }

  const handles: ResizeHandle[] = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w']

  return (
    <>
      {handles.map((handle) => (
        <div
          key={handle}
          style={handleStyle(handle)}
          onMouseDown={(e) => handleMouseDown(handle, e)}
        />
      ))}
    </>
  )
}
