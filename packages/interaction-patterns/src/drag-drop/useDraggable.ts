import { useRef, useState, useEffect } from 'react'

/**
 * Options for configuring draggable behavior
 */
export interface DraggableOptions {
  /** Initial position of the element */
  initialPosition?: { x: number; y: number }
  /** Callback fired when dragging ends */
  onDragEnd?: (position: { x: number; y: number }) => void
  /** Boundaries to constrain dragging */
  bounds?: 'parent' | 'window' | { top: number; left: number; right: number; bottom: number }
  /** CSS selector for drag handle (if specified, only this element can initiate drag) */
  handle?: string
}

/**
 * Return value from useDraggable hook
 */
export interface DraggableResult {
  /** Ref to attach to the draggable element */
  ref: React.RefObject<HTMLDivElement | null>
  /** Current position of the element */
  position: { x: number; y: number }
  /** Whether the element is currently being dragged */
  isDragging: boolean
  /** Programmatically set the position */
  setPosition: (position: { x: number; y: number }) => void
  /** Pre-configured style object for the draggable element */
  style: {
    position: 'absolute'
    left: number
    top: number
    cursor: 'grabbing' | 'grab'
    userSelect: 'none' | 'auto'
  }
}

/**
 * Make any element draggable
 *
 * @example
 * ```tsx
 * function DraggableCard() {
 *   const { ref, position, isDragging } = useDraggable({
 *     initialPosition: { x: 100, y: 100 },
 *     onDragEnd: (pos) => console.log('Dropped at', pos)
 *   })
 *
 *   return (
 *     <div ref={ref} style={{
 *       position: 'absolute',
 *       left: position.x,
 *       top: position.y,
 *       cursor: isDragging ? 'grabbing' : 'grab'
 *     }}>
 *       Drag me!
 *     </div>
 *   )
 * }
 * ```
 *
 * Features:
 * - Automatic boundary detection (window or parent)
 * - Prevents dragging from interactive elements (buttons, links, inputs)
 * - Optional drag handle for title-bar-style dragging
 * - Smooth dragging with proper cleanup
 * - Accessible by default (preserves text selection when not dragging)
 */
export function useDraggable({
  initialPosition = { x: 0, y: 0 },
  onDragEnd,
  bounds = 'window',
  handle,
}: DraggableOptions = {}): DraggableResult {
  const elementRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState(initialPosition)
  const [isDragging, setIsDragging] = useState(false)
  const dragStartPos = useRef({ x: 0, y: 0 })
  const elementStartPos = useRef({ x: 0, y: 0 })
  const currentPosition = useRef(initialPosition)
  const boundsRef = useRef(bounds)
  const onDragEndRef = useRef(onDragEnd)
  const dragThreshold = 5 // Minimum pixels to move before drag starts
  const hasDraggedBeyondThreshold = useRef(false)

  // Keep refs in sync
  useEffect(() => {
    currentPosition.current = position
  }, [position])

  useEffect(() => {
    boundsRef.current = bounds
  }, [bounds])

  useEffect(() => {
    onDragEndRef.current = onDragEnd
  }, [onDragEnd])

  useEffect(() => {
    const element = elementRef.current
    if (!element) return

    const handleMouseDown = (e: MouseEvent) => {
      // Check if we should start dragging
      const target = e.target as HTMLElement

      // Don't drag from interactive elements (buttons, links, inputs)
      if (
        target.tagName === 'BUTTON' ||
        target.tagName === 'A' ||
        target.tagName === 'INPUT' ||
        target.tagName === 'TEXTAREA' ||
        target.tagName === 'SELECT' ||
        target.closest('button, a, input, textarea, select')
      ) {
        return
      }

      // If handle is specified, only drag from handle
      if (handle) {
        const handleElement = element.querySelector(handle)
        if (!handleElement?.contains(target)) return
      }

      // Don't prevent default immediately - wait for drag threshold
      // This allows click events to work properly

      dragStartPos.current = { x: e.clientX, y: e.clientY }
      elementStartPos.current = { ...currentPosition.current }
      hasDraggedBeyondThreshold.current = false

      // Add global listeners
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    const handleMouseMove = (e: MouseEvent) => {
      if (!elementRef.current) return

      const deltaX = e.clientX - dragStartPos.current.x
      const deltaY = e.clientY - dragStartPos.current.y

      // Check if we've moved beyond threshold
      if (!hasDraggedBeyondThreshold.current) {
        const distance = Math.sqrt(deltaX * deltaX + deltaY * deltaY)
        if (distance < dragThreshold) {
          return // Don't start dragging yet
        }
        // We've crossed the threshold, start dragging
        hasDraggedBeyondThreshold.current = true
        setIsDragging(true)
        // Prevent text selection when actually dragging
        e.preventDefault()
      }

      let newX = elementStartPos.current.x + deltaX
      let newY = elementStartPos.current.y + deltaY

      // Apply bounds
      if (boundsRef.current === 'window') {
        const rect = elementRef.current.getBoundingClientRect()
        newX = Math.max(0, Math.min(newX, window.innerWidth - rect.width))
        newY = Math.max(0, Math.min(newY, window.innerHeight - rect.height))
      } else if (boundsRef.current === 'parent' && elementRef.current.parentElement) {
        const parentRect = elementRef.current.parentElement.getBoundingClientRect()
        const rect = elementRef.current.getBoundingClientRect()
        newX = Math.max(0, Math.min(newX, parentRect.width - rect.width))
        newY = Math.max(0, Math.min(newY, parentRect.height - rect.height))
      } else if (typeof boundsRef.current === 'object') {
        newX = Math.max(boundsRef.current.left, Math.min(newX, boundsRef.current.right))
        newY = Math.max(boundsRef.current.top, Math.min(newY, boundsRef.current.bottom))
      }

      setPosition({ x: newX, y: newY })
    }

    const handleMouseUp = () => {
      const wasDragging = hasDraggedBeyondThreshold.current

      setIsDragging(false)
      hasDraggedBeyondThreshold.current = false
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)

      // Only fire onDragEnd if we actually dragged beyond threshold
      if (wasDragging && onDragEndRef.current) {
        onDragEndRef.current(currentPosition.current)
      }
    }

    element.addEventListener('mousedown', handleMouseDown)

    return () => {
      element.removeEventListener('mousedown', handleMouseDown)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)
    }
  }, [handle]) // Only re-register when handle changes

  return {
    ref: elementRef,
    position,
    isDragging,
    setPosition,
    style: {
      position: 'absolute' as const,
      left: position.x,
      top: position.y,
      cursor: isDragging ? 'grabbing' : 'grab',
      userSelect: isDragging ? 'none' as const : 'auto' as const,
    },
  }
}
