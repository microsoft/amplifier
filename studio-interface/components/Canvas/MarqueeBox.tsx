'use client'

import { useStudioStore } from '@/state/store'

/**
 * Marquee Selection Box
 * Visual feedback for drag-to-select
 * Shows which artifacts will be selected
 */
export function MarqueeBox() {
  const marquee = useStudioStore((state) => state.marquee)
  const getMarqueeRect = useStudioStore((state) => state.getMarqueeRect)

  if (!marquee.active || !marquee.start || !marquee.end) {
    return null
  }

  const rect = getMarqueeRect()
  if (!rect) return null

  return (
    <div
      className="marquee-box"
      style={{
        position: 'absolute',
        left: rect.x,
        top: rect.y,
        width: rect.width,
        height: rect.height,
        border: '1px solid var(--primary)',
        background: 'var(--color-primary-subtle)',
        borderRadius: '4px',
        pointerEvents: 'none',
        zIndex: 500,
        animation: 'marquee-appear 100ms cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    />
  )
}