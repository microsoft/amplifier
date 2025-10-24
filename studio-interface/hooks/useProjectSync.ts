import { useEffect, useRef } from 'react'
import { useStudioStore } from '@/state/store'

/**
 * Hook to auto-save project state to Supabase
 * Debounces saves to avoid excessive API calls
 */
export function useProjectSync(debounceMs: number = 2000) {
  const saveProject = useStudioStore((state) => state.saveProject)
  const project = useStudioStore((state) => state.project)
  const phase = useStudioStore((state) => state.phase)
  const canvasArtifacts = useStudioStore((state) => state.canvasArtifacts)
  const messages = useStudioStore((state) => state.messages)

  const saveTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const lastSaveRef = useRef<string>('')

  useEffect(() => {
    // Don't auto-save if no project
    if (!project) return

    // Create a snapshot of current state to detect changes
    const currentSnapshot = JSON.stringify({
      phase,
      artifactsCount: canvasArtifacts.length,
      messagesCount: messages.length,
      context: project.context,
    })

    // Skip if nothing changed
    if (currentSnapshot === lastSaveRef.current) return

    lastSaveRef.current = currentSnapshot

    // Clear any pending save
    if (saveTimeoutRef.current) {
      clearTimeout(saveTimeoutRef.current)
    }

    // Schedule a new save
    saveTimeoutRef.current = setTimeout(() => {
      saveProject().catch((error) => {
        console.error('Failed to auto-save project:', error)
      })
    }, debounceMs)

    // Cleanup on unmount
    return () => {
      if (saveTimeoutRef.current) {
        clearTimeout(saveTimeoutRef.current)
      }
    }
  }, [project, phase, canvasArtifacts, messages, saveProject, debounceMs])
}
