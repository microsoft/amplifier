'use client'

import React from 'react'
import { useStudioStore, type StudioPhase } from '@/state/store'
import { CheckIcon, SearchIcon, GridIcon, LayersIcon, BoxIcon } from './icons/Icon'
import { Tooltip } from './Tooltip'

/**
 * Phase Navigator
 * Icon-only navigation with tooltips
 * Shows all 4 phases with progressive unlock
 * Visual indicators for current, completed, locked states
 */

interface PhaseInfo {
  id: Exclude<StudioPhase, 'empty'>
  name: string
  icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>
}

const PHASES: PhaseInfo[] = [
  {
    id: 'discover',
    name: 'Discovery',
    icon: SearchIcon,
  },
  {
    id: 'explore',
    name: 'Exploration',
    icon: GridIcon,
  },
  {
    id: 'express',
    name: 'Expression',
    icon: LayersIcon,
  },
  {
    id: 'create',
    name: 'Delivery',
    icon: BoxIcon,
  },
]

export function PhaseNavigator() {
  const phase = useStudioStore((state) => state.phase)
  const setPhase = useStudioStore((state) => state.setPhase)
  const phaseReadiness = useStudioStore((state) => state.phaseReadiness)

  const handlePhaseClick = (phaseId: Exclude<StudioPhase, 'empty'>) => {
    // Only navigate if phase is unlocked
    if (phaseReadiness[phaseId]) {
      setPhase(phaseId)
    }
  }

  const isPhaseComplete = (phaseId: Exclude<StudioPhase, 'empty'>) => {
    const phaseIndex = PHASES.findIndex((p) => p.id === phaseId)
    const currentPhaseIndex = PHASES.findIndex((p) => p.id === phase)
    return phaseIndex < currentPhaseIndex
  }

  const currentIndex = PHASES.findIndex((p) => p.id === phase)

  return (
    <div
      style={{
        display: 'inline-flex',
        background: 'var(--bg-secondary)',
        borderRadius: '10px',
        padding: '4px',
        gap: '2px',
        position: 'relative',
        border: '1px solid var(--border)',
      }}
    >
      {/* Sliding indicator */}
      <div
        style={{
          position: 'absolute',
          top: '4px',
          left: `calc(4px + ${currentIndex * 38}px)`, // 36px button + 2px gap
          width: '36px',
          height: '36px',
          background: 'var(--bg-primary)',
          borderRadius: '6px',
          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.08)',
          transition: 'left 300ms cubic-bezier(0.34, 1.56, 0.64, 1)',
          pointerEvents: 'none',
          zIndex: 0,
        }}
      />

      {PHASES.map((phaseInfo, index) => {
        const isCurrent = phase === phaseInfo.id
        const isUnlocked = phaseReadiness[phaseInfo.id]
        const isComplete = isPhaseComplete(phaseInfo.id)

        const PhaseIcon = phaseInfo.icon

        return (
          <Tooltip key={phaseInfo.id} content={phaseInfo.name} side="bottom">
            <button
              onClick={() => handlePhaseClick(phaseInfo.id)}
              disabled={!isUnlocked}
              style={{
                width: '36px',
                height: '36px',
                background: isUnlocked ? 'transparent' : 'var(--bg-secondary)',
                border: isUnlocked ? 'none' : '1px solid transparent',
                cursor: isUnlocked ? 'pointer' : 'not-allowed',
                opacity: isUnlocked ? 1 : 0.4,
                transition: 'all 100ms ease',
                color: isCurrent ? 'var(--text-primary)' : 'var(--text-muted)',
                position: 'relative',
                zIndex: 1,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                borderRadius: '6px',
              }}
              onMouseEnter={(e) => {
                if (!isUnlocked) {
                  e.currentTarget.style.opacity = '0.5'
                  e.currentTarget.style.background = 'var(--color-hover)'
                  e.currentTarget.style.borderColor = 'var(--border)'
                }
              }}
              onMouseLeave={(e) => {
                if (!isUnlocked) {
                  e.currentTarget.style.opacity = '0.4'
                  e.currentTarget.style.background = 'var(--bg-secondary)'
                  e.currentTarget.style.borderColor = 'transparent'
                }
              }}
            >
              <PhaseIcon size={18} strokeWidth={1.5} />

              {/* Status indicator dot */}
              {isComplete && (
                <div
                  style={{
                    position: 'absolute',
                    top: '4px',
                    right: '4px',
                    width: '6px',
                    height: '6px',
                    borderRadius: '50%',
                    background: 'var(--success-color, #22c55e)',
                  }}
                />
              )}
            </button>
          </Tooltip>
        )
      })}
    </div>
  )
}
