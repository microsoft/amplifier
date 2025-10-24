import { useState, useCallback, useEffect, useRef } from 'react'

interface CanvasTransform {
  x: number
  y: number
  scale: number
}

interface UseCanvasTransformOptions {
  minScale?: number
  maxScale?: number
  initialScale?: number
}

export function useCanvasTransform(options: UseCanvasTransformOptions = {}) {
  const {
    minScale = 0.1,
    maxScale = 4,
    initialScale = 1,
  } = options

  const [transform, setTransform] = useState<CanvasTransform>({
    x: 0,
    y: 0,
    scale: initialScale,
  })

  const [isPanning, setIsPanning] = useState(false)
  const panStartRef = useRef({ x: 0, y: 0 })
  const transformRef = useRef(transform)

  // Keep ref in sync with state
  useEffect(() => {
    transformRef.current = transform
  }, [transform])

  // Zoom to a specific point
  const zoomTo = useCallback((newScale: number, centerX: number, centerY: number) => {
    setTransform((prev) => {
      const clampedScale = Math.max(minScale, Math.min(maxScale, newScale))
      const scaleDiff = clampedScale / prev.scale

      // Zoom towards the point (centerX, centerY)
      const newX = centerX - (centerX - prev.x) * scaleDiff
      const newY = centerY - (centerY - prev.y) * scaleDiff

      return {
        x: newX,
        y: newY,
        scale: clampedScale,
      }
    })
  }, [minScale, maxScale])

  // Zoom in/out by delta
  const zoom = useCallback((delta: number, centerX?: number, centerY?: number) => {
    const factor = delta > 0 ? 1.1 : 0.9
    const cx = centerX ?? window.innerWidth / 2
    const cy = centerY ?? window.innerHeight / 2
    zoomTo(transformRef.current.scale * factor, cx, cy)
  }, [zoomTo])

  // Pan by delta
  const pan = useCallback((deltaX: number, deltaY: number) => {
    setTransform((prev) => ({
      ...prev,
      x: prev.x + deltaX,
      y: prev.y + deltaY,
    }))
  }, [])

  // Reset to initial state
  const reset = useCallback(() => {
    setTransform({
      x: 0,
      y: 0,
      scale: initialScale,
    })
  }, [initialScale])

  // Zoom to fit content
  const zoomToFit = useCallback((contentBounds: { width: number; height: number; x: number; y: number }, containerBounds: { width: number; height: number }) => {
    const padding = 80
    const scaleX = (containerBounds.width - padding * 2) / contentBounds.width
    const scaleY = (containerBounds.height - padding * 2) / contentBounds.height
    const newScale = Math.max(minScale, Math.min(maxScale, Math.min(scaleX, scaleY)))

    const centerX = containerBounds.width / 2
    const centerY = containerBounds.height / 2
    const contentCenterX = contentBounds.x + contentBounds.width / 2
    const contentCenterY = contentBounds.y + contentBounds.height / 2

    setTransform({
      x: centerX - contentCenterX * newScale,
      y: centerY - contentCenterY * newScale,
      scale: newScale,
    })
  }, [minScale, maxScale])

  // Handle mouse/trackpad wheel events
  const handleWheel = useCallback((e: WheelEvent) => {
    e.preventDefault()

    // Check if this is a pinch gesture (ctrlKey is set for trackpad pinch)
    if (e.ctrlKey) {
      // Pinch to zoom
      const delta = -e.deltaY
      zoom(delta, e.clientX, e.clientY)
    } else {
      // Two-finger pan on trackpad or shift+scroll
      pan(-e.deltaX, -e.deltaY)
    }
  }, [zoom, pan])

  // Handle mouse pan (space + drag or middle mouse button)
  const handleMouseDown = useCallback((e: MouseEvent) => {
    // Space + drag or middle mouse button
    if (e.button === 1 || (e.button === 0 && e.shiftKey)) {
      e.preventDefault()
      setIsPanning(true)
      panStartRef.current = { x: e.clientX, y: e.clientY }
    }
  }, [])

  const handleMouseMove = useCallback((e: MouseEvent) => {
    if (!isPanning) return

    const deltaX = e.clientX - panStartRef.current.x
    const deltaY = e.clientY - panStartRef.current.y

    pan(deltaX, deltaY)

    panStartRef.current = { x: e.clientX, y: e.clientY }
  }, [isPanning, pan])

  const handleMouseUp = useCallback(() => {
    setIsPanning(false)
  }, [])

  // Keyboard shortcuts
  const handleKeyDown = useCallback((e: KeyboardEvent) => {
    // Cmd/Ctrl + 0: Reset zoom
    if ((e.metaKey || e.ctrlKey) && e.key === '0') {
      e.preventDefault()
      reset()
    }

    // Cmd/Ctrl + Plus/Equals: Zoom in
    if ((e.metaKey || e.ctrlKey) && (e.key === '+' || e.key === '=')) {
      e.preventDefault()
      zoom(1)
    }

    // Cmd/Ctrl + Minus: Zoom out
    if ((e.metaKey || e.ctrlKey) && e.key === '-') {
      e.preventDefault()
      zoom(-1)
    }

    // Cmd/Ctrl + 1: Zoom to 100%
    if ((e.metaKey || e.ctrlKey) && e.key === '1') {
      e.preventDefault()
      setTransform((prev) => ({ ...prev, scale: 1 }))
    }
  }, [zoom, reset])

  return {
    transform,
    isPanning,
    zoom,
    pan,
    reset,
    zoomToFit,
    handlers: {
      onWheel: handleWheel,
      onMouseDown: handleMouseDown,
      onMouseMove: handleMouseMove,
      onMouseUp: handleMouseUp,
      onKeyDown: handleKeyDown,
    },
  }
}
