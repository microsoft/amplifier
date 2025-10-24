import { useRef, useState, useEffect } from 'react'

interface DraggableOptions {
  initialPosition?: { x: number; y: number }
  onDragEnd?: (position: { x: number; y: number }) => void
  bounds?: 'parent' | 'window' | { top: number; left: number; right: number; bottom: number }
  handle?: string // CSS selector for drag handle
}

export function useDraggable({
  initialPosition = { x: 0, y: 0 },
  onDragEnd,
  bounds = 'window',
  handle,
}: DraggableOptions = {}) {
  const elementRef = useRef<HTMLDivElement>(null)
  const [position, setPosition] = useState(initialPosition)
  const [isDragging, setIsDragging] = useState(false)
  const dragStartPos = useRef({ x: 0, y: 0 })
  const elementStartPos = useRef({ x: 0, y: 0 })
  const currentPosition = useRef(initialPosition)
  const boundsRef = useRef(bounds)
  const onDragEndRef = useRef(onDragEnd)

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

      // Prevent text selection during drag
      e.preventDefault()

      setIsDragging(true)
      dragStartPos.current = { x: e.clientX, y: e.clientY }
      elementStartPos.current = { ...currentPosition.current }

      // Add global listeners
      document.addEventListener('mousemove', handleMouseMove)
      document.addEventListener('mouseup', handleMouseUp)
    }

    const handleMouseMove = (e: MouseEvent) => {
      if (!elementRef.current) return

      const deltaX = e.clientX - dragStartPos.current.x
      const deltaY = e.clientY - dragStartPos.current.y

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
      setIsDragging(false)
      document.removeEventListener('mousemove', handleMouseMove)
      document.removeEventListener('mouseup', handleMouseUp)

      // Use the ref to get the latest position
      if (onDragEndRef.current) {
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
