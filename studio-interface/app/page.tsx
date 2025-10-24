'use client'

import { useState, useEffect } from 'react'
import { useStudioStore } from '@/state/store'
import { useProjectSync } from '@/hooks/useProjectSync'
import { EmptyState } from '@/components/EmptyState'
import { DiscoveryWorkspaceV2 } from '@/components/DiscoveryWorkspaceV2'
import { ExpressionWorkspace } from '@/components/ExpressionWorkspace'

/**
 * Studio Interface - Main Router
 * Routes between phases: empty → discover → explore → express → create
 */
export default function Studio() {
  const phase = useStudioStore((state) => state.phase)
  const [displayPhase, setDisplayPhase] = useState(phase)
  const [isTransitioning, setIsTransitioning] = useState(false)

  // Auto-save project state to Supabase (debounced)
  useProjectSync()

  // Handle phase transitions with animation
  useEffect(() => {
    if (phase !== displayPhase) {
      setIsTransitioning(true)

      // Fade out current phase
      setTimeout(() => {
        setDisplayPhase(phase)
        setIsTransitioning(false)
      }, 350) // 300ms fade out + 50ms breath
    }
  }, [phase, displayPhase])

  // Wrapper for transition animations
  const getPhaseComponent = () => {
    switch (displayPhase) {
      case 'empty':
        return <EmptyState />

      case 'discover':
        return <DiscoveryWorkspaceV2 />

      case 'explore':
        // TODO: Build explore phase (brainstorming/alternatives)
        return <div>Explore phase - Coming soon</div>

      case 'express':
        return <ExpressionWorkspace />

      case 'create':
        // TODO: Build create phase (final deliverables)
        return <div>Create phase - Coming soon</div>

      default:
        return <EmptyState />
    }
  }

  return (
    <div
      style={{
        width: '100%',
        height: '100%',
        opacity: isTransitioning ? 0 : 1,
        transform: isTransitioning ? 'scale(0.98)' : 'scale(1)',
        transition: 'opacity 300ms cubic-bezier(0.4, 0, 0.2, 1), transform 300ms cubic-bezier(0.4, 0, 0.2, 1)',
      }}
    >
      {getPhaseComponent()}
    </div>
  )
}
