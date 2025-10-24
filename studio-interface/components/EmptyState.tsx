'use client'

import { useState, useEffect, useRef } from 'react'
import { useStudioStore } from '@/state/store'
import { useProject } from '@/lib/hooks/useProject'
import { useAuth } from '@/lib/hooks/useAuth'
import { AuthModal } from './AuthModal'

/**
 * Empty State - First thing user sees
 * Clean invitation to start creating
 */
// Fun color palettes inspired by Swedish design studios
const COLOR_PALETTES = [
  // Default neutral - starts with eerie black
  { bg: '#F8F9F6', text: '#1C1C1C', accent: '#1C1C1C', gradient: 'rgba(28, 28, 28, 0.03)' },
  // Playful coral & teal
  { bg: '#FFF5F0', text: '#FF6B6B', accent: '#4ECDC4', gradient: 'rgba(78, 205, 196, 0.12)' },
  // Swedish summer
  { bg: '#FFFBEB', text: '#F59E0B', accent: '#10B981', gradient: 'rgba(16, 185, 129, 0.12)' },
  // Nordic berry
  { bg: '#FDF2F8', text: '#DB2777', accent: '#8B5CF6', gradient: 'rgba(139, 92, 246, 0.12)' },
  // Ocean depth
  { bg: '#F0F9FF', text: '#0284C7', accent: '#7C3AED', gradient: 'rgba(124, 58, 237, 0.12)' },
  // Sunset glow
  { bg: '#FFF7ED', text: '#EA580C', accent: '#EC4899', gradient: 'rgba(236, 72, 153, 0.12)' },
  // Forest green
  { bg: '#F0FDF4', text: '#059669', accent: '#6366F1', gradient: 'rgba(99, 102, 241, 0.12)' },
  // Electric purple
  { bg: '#FAF5FF', text: '#9333EA', accent: '#F59E0B', gradient: 'rgba(245, 158, 11, 0.12)' },
  // Sky blue
  { bg: '#F0F9FF', text: '#0EA5E9', accent: '#F43F5E', gradient: 'rgba(244, 63, 94, 0.12)' },
  // Candy pink
  { bg: '#FFF1F2', text: '#FB7185', accent: '#06B6D4', gradient: 'rgba(6, 182, 212, 0.12)' },
]

export function EmptyState() {
  const setPhase = useStudioStore((state) => state.setPhase)
  const updatePhaseReadiness = useStudioStore((state) => state.updatePhaseReadiness)
  const { createProject } = useProject()
  const { user } = useAuth()
  const [isCreating, setIsCreating] = useState(false)
  const [mousePosition, setMousePosition] = useState({ x: 0.5, y: 0.5 })
  const [hasAnimated, setHasAnimated] = useState(false)
  const [showAuthModal, setShowAuthModal] = useState(false)
  // Always start with base theme (index 0)
  const [currentPaletteIndex, setCurrentPaletteIndex] = useState(0)
  const studioRef = useRef<HTMLSpanElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  const handleStartProject = async () => {
    // Check if user is authenticated
    if (!user) {
      setShowAuthModal(true)
      return
    }

    setIsCreating(true)
    try {
      // Create project in database
      await createProject('Untitled Project')
      // Unlock discover phase and move to it
      updatePhaseReadiness('discover', true)
      setPhase('discover')
    } catch (error) {
      console.error('Failed to create project:', error)
      setIsCreating(false)
    }
  }

  // Track mouse position for background gradient
  useEffect(() => {
    const handleMouseMove = (e: MouseEvent) => {
      if (containerRef.current) {
        const rect = containerRef.current.getBoundingClientRect()
        setMousePosition({
          x: (e.clientX - rect.left) / rect.width,
          y: (e.clientY - rect.top) / rect.height,
        })
      }
    }

    const container = containerRef.current
    if (container) {
      container.addEventListener('mousemove', handleMouseMove)
      return () => container.removeEventListener('mousemove', handleMouseMove)
    }
  }, [])

  // Auto-fire letter cascade on mount
  useEffect(() => {
    if (!hasAnimated && studioRef.current) {
      setTimeout(() => {
        const letters = studioRef.current?.querySelectorAll('span')
        if (letters) {
          letters.forEach((letter, index) => {
            setTimeout(() => {
              (letter as HTMLElement).style.transform = 'translateY(-6px)'

              // When the "o" (last letter, index 5) reaches its peak, trigger the color ripple
              if (index === 5) {
                setTimeout(() => {
                  // Switch to a random different palette - creates ripple effect
                  setCurrentPaletteIndex((prev) => {
                    let newIndex
                    do {
                      newIndex = Math.floor(Math.random() * COLOR_PALETTES.length)
                    } while (newIndex === prev)
                    return newIndex
                  })
                }, 100) // Trigger right as it starts coming down
              }

              setTimeout(() => {
                (letter as HTMLElement).style.transform = 'translateY(0)'
              }, 300)
            }, index * 60)
          })
        }
        setHasAnimated(true)
      }, 600) // Fire after initial fade-in
    }
  }, [hasAnimated])

  const triggerCascade = () => {
    if (studioRef.current) {
      const letters = studioRef.current.querySelectorAll('span')
      letters.forEach((letter, index) => {
        setTimeout(() => {
          (letter as HTMLElement).style.transform = 'translateY(-6px)'
          setTimeout(() => {
            (letter as HTMLElement).style.transform = 'translateY(0)'
          }, 300)
        }, index * 60)
      })
    }
  }

  const handleStudioHover = () => {
    // Pick a random palette (excluding current one)
    let newIndex
    do {
      newIndex = Math.floor(Math.random() * COLOR_PALETTES.length)
    } while (newIndex === currentPaletteIndex)
    setCurrentPaletteIndex(newIndex)
    triggerCascade()
  }

  const currentPalette = COLOR_PALETTES[currentPaletteIndex]

  return (
    <div
      ref={containerRef}
      className="flex h-screen w-screen items-center justify-center studio-canvas"
      style={{
        backgroundColor: currentPalette.bg,
        backgroundImage: `radial-gradient(circle at ${mousePosition.x * 100}% ${mousePosition.y * 100}%, ${currentPalette.gradient} 0%, transparent 50%)`,
        transition: 'all 500ms cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      <div className="text-center fade-in" style={{ maxWidth: '560px', padding: '48px' }}>
        <h1
          className="font-heading"
          style={{
            fontSize: '48px',
            fontWeight: 700,
            marginBottom: '24px',
            letterSpacing: '-0.02em',
            color: currentPalette.text,
            transition: 'color 500ms cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          Welcome to{' '}
          <span
            ref={studioRef}
            style={{
              display: 'inline-block',
              cursor: 'pointer',
              color: currentPalette.accent,
              transition: 'color 500ms cubic-bezier(0.4, 0, 0.2, 1)',
            }}
            onMouseEnter={handleStudioHover}
          >
            {'Studio'.split('').map((letter, index) => (
              <span
                key={index}
                style={{
                  display: 'inline-block',
                  transition: 'transform 300ms cubic-bezier(0.34, 1.56, 0.64, 1)',
                }}
              >
                {letter}
              </span>
            ))}
          </span>
        </h1>

        <p
          style={{
            fontSize: '18px',
            lineHeight: '1.6',
            color: 'var(--text-muted)',
            marginBottom: '48px'
          }}
        >
          Your design partner that transforms intent into expression—working with you to
          create bespoke solutions that serve your purpose.
        </p>

        <button
          className="studio-button studio-button-lg"
          onClick={handleStartProject}
          disabled={isCreating}
          style={{
            opacity: isCreating ? 0.5 : 1,
            backgroundColor: currentPalette.accent,
            color: 'white',
            border: 'none',
            transition: 'all 500ms cubic-bezier(0.4, 0, 0.2, 1)',
          }}
          onMouseEnter={(e) => {
            if (!isCreating) {
              e.currentTarget.style.transform = 'translateY(-2px) scale(1.02)'
              e.currentTarget.style.boxShadow = `0 8px 16px ${currentPalette.accent}40`
            }
          }}
          onMouseLeave={(e) => {
            e.currentTarget.style.transform = 'translateY(0) scale(1)'
            e.currentTarget.style.boxShadow = 'none'
          }}
        >
          {isCreating ? 'Starting...' : 'Start New Project'}
        </button>

        <p
          style={{
            fontSize: '13px',
            color: 'var(--text-muted)',
            marginTop: '32px',
            opacity: 0.6
          }}
        >
          I&rsquo;ll guide you through a thoughtful discovery process
        </p>
      </div>

      {/* Auth Modal */}
      <AuthModal
        isOpen={showAuthModal}
        onClose={() => setShowAuthModal(false)}
      />
    </div>
  )
}
