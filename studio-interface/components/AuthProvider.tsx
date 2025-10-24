'use client'

import { useEffect, useState } from 'react'
import { useAuth } from '@/lib/hooks/useAuth'
import { useStudioStore } from '@/state/store'

/**
 * Auth Provider - Manages authentication state
 *
 * Note: Projects are NOT auto-loaded on auth. Users start at the empty state
 * and explicitly choose to create a new project or load an existing one.
 */
export function AuthProvider({ children }: { children: React.ReactNode }) {
  const { user, loading: authLoading } = useAuth()
  const setPhase = useStudioStore((state) => state.setPhase)
  const setProject = useStudioStore((state) => state.setProject)

  useEffect(() => {
    if (!authLoading && !user) {
      // User logged out, reset to empty state
      setPhase('empty')
      setProject(null)
    }
  }, [user, authLoading, setPhase, setProject])

  return <>{children}</>
}
