'use client'

import { useState, useRef, useEffect } from 'react'

interface TooltipProps {
  content: string
  children: React.ReactElement
  side?: 'top' | 'bottom' | 'left' | 'right'
  delay?: number
}

/**
 * Tooltip - Design system component
 * Appears on hover with configurable side and delay
 * Uses relative positioning to avoid offset issues
 */
export function Tooltip({ content, children, side = 'bottom', delay = 300 }: TooltipProps) {
  const [isVisible, setIsVisible] = useState(false)
  const timeoutRef = useRef<NodeJS.Timeout>()

  const handleMouseEnter = () => {
    timeoutRef.current = setTimeout(() => {
      setIsVisible(true)
    }, delay)
  }

  const handleMouseLeave = () => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current)
    }
    setIsVisible(false)
  }

  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current)
      }
    }
  }, [])

  // Calculate positioning styles based on side
  const getTooltipStyles = () => {
    const baseStyles = {
      position: 'absolute' as const,
      padding: 'var(--space-1-5) var(--space-3)',
      fontSize: '13px',
      fontFamily: 'var(--font-geist-sans)',
      color: 'var(--text-primary)',
      background: 'var(--bg-primary)',
      border: '1px solid var(--border)',
      borderRadius: 'var(--radius-md)',
      boxShadow: 'var(--shadow-elevated)',
      pointerEvents: 'none' as const,
      zIndex: 10000,
      whiteSpace: 'nowrap' as const,
      opacity: isVisible ? 1 : 0,
      transition: 'opacity 150ms ease',
    }

    const offset = 8 // Space between trigger and tooltip

    switch (side) {
      case 'top':
        return {
          ...baseStyles,
          bottom: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginBottom: `${offset}px`,
        }
      case 'bottom':
        return {
          ...baseStyles,
          top: '100%',
          left: '50%',
          transform: 'translateX(-50%)',
          marginTop: `${offset}px`,
        }
      case 'left':
        return {
          ...baseStyles,
          right: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          marginRight: `${offset}px`,
        }
      case 'right':
        return {
          ...baseStyles,
          left: '100%',
          top: '50%',
          transform: 'translateY(-50%)',
          marginLeft: `${offset}px`,
        }
      default:
        return baseStyles
    }
  }

  return (
    <div
      onMouseEnter={handleMouseEnter}
      onMouseLeave={handleMouseLeave}
      style={{ position: 'relative', display: 'inline-flex' }}
    >
      {children}

      {isVisible && (
        <div style={getTooltipStyles()}>
          {content}
        </div>
      )}
    </div>
  )
}
