import { useEffect } from 'react'
import { supabase } from '@/lib/supabase'
import { useStudioStore } from '@/state/store'

/**
 * Project persistence hook
 * Syncs project state with Supabase
 */
export function useProject() {
  const { project, setProject, messages } = useStudioStore()

  // Create a new project
  const createProject = async (name: string) => {
    // Get current user
    const { data: { user } } = await supabase.auth.getUser()

    if (!user) {
      console.error('No authenticated user')
      throw new Error('You must be signed in to create a project')
    }

    const { data, error } = await supabase
      .from('projects')
      .insert({
        user_id: user.id,
        name,
        status: 'discovery',
        context: {},
      })
      .select()
      .single()

    if (error) {
      console.error('Failed to create project:', error)
      throw error
    }

    setProject({
      id: data.id,
      name: data.name,
      content: '',
      context: data.context,
    })

    return data
  }

  // Update project context
  const updateProjectContext = async (context: Record<string, unknown>) => {
    if (!project) return
    // TEMPORARY: Skip database persistence
    console.log('Update project context (not persisted):', context)
  }

  // Update project status
  const updateProjectStatus = async (status: 'discovery' | 'expression' | 'completed') => {
    if (!project) return
    // TEMPORARY: Skip database persistence
    console.log('Update project status (not persisted):', status)
  }

  // Save message to database
  const saveMessage = async (role: 'user' | 'ai', content: string) => {
    if (!project) return
    // TEMPORARY: Skip database persistence
    console.log('Save message (not persisted):', { role, content: content.substring(0, 50) + '...' })
  }

  // Load project messages
  const loadMessages = async (projectId: string) => {
    const { data, error } = await supabase
      .from('messages')
      .select('*')
      .eq('project_id', projectId)
      .order('created_at', { ascending: true })

    if (error) {
      console.error('Failed to load messages:', error)
      return []
    }

    return data
  }

  return {
    project,
    createProject,
    updateProjectContext,
    updateProjectStatus,
    saveMessage,
    loadMessages,
  }
}
