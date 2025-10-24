import { supabase } from './supabase'
import type { Database } from './supabase'
import type { DiscoveryContext, Message, CanvasArtifact } from '@/state/store'

type ProjectRow = Database['public']['Tables']['projects']['Row']
type ProjectInsert = Database['public']['Tables']['projects']['Insert']
type ProjectUpdate = Database['public']['Tables']['projects']['Update']

type MessageRow = Database['public']['Tables']['messages']['Row']
type MessageInsert = Database['public']['Tables']['messages']['Insert']

type DesignVersionRow = Database['public']['Tables']['design_versions']['Row']
type DesignVersionInsert = Database['public']['Tables']['design_versions']['Insert']

/**
 * Extended project type with full application state
 */
export interface ProjectData {
  id: string
  name: string
  status: 'discovery' | 'expression' | 'completed'
  context: DiscoveryContext & {
    canvasArtifacts?: CanvasArtifact[]
    phase?: string
    phaseReadiness?: Record<string, boolean>
  }
  created_at: string
  updated_at: string
}

/**
 * Project persistence layer
 */
export const projectsApi = {
  /**
   * Get all projects for the current user
   */
  async list(): Promise<ProjectData[]> {
    const { data, error } = await supabase
      .from('projects')
      .select('*')
      .order('updated_at', { ascending: false })

    if (error) throw error
    return data as ProjectData[]
  },

  /**
   * Get a single project by ID
   */
  async get(id: string): Promise<ProjectData | null> {
    const { data, error } = await supabase
      .from('projects')
      .select('*')
      .eq('id', id)
      .single()

    if (error) {
      if (error.code === 'PGRST116') return null // Not found
      throw error
    }
    return data as ProjectData
  },

  /**
   * Create a new project
   */
  async create(
    userId: string,
    name: string,
    context: ProjectData['context'] = {}
  ): Promise<ProjectData> {
    const { data, error } = await supabase
      .from('projects')
      .insert({
        user_id: userId,
        name,
        status: 'discovery',
        context,
      })
      .select()
      .single()

    if (error) throw error
    return data as ProjectData
  },

  /**
   * Update an existing project
   */
  async update(
    id: string,
    updates: {
      name?: string
      status?: ProjectData['status']
      context?: ProjectData['context']
    }
  ): Promise<ProjectData> {
    const { data, error } = await supabase
      .from('projects')
      .update(updates)
      .eq('id', id)
      .select()
      .single()

    if (error) throw error
    return data as ProjectData
  },

  /**
   * Delete a project
   */
  async delete(id: string): Promise<void> {
    const { error } = await supabase.from('projects').delete().eq('id', id)

    if (error) throw error
  },

  /**
   * Save full project state (context, artifacts, phase, etc.)
   */
  async saveState(
    id: string,
    state: {
      context?: DiscoveryContext
      canvasArtifacts?: CanvasArtifact[]
      phase?: string
      phaseReadiness?: Record<string, boolean>
      status?: ProjectData['status']
    }
  ): Promise<void> {
    // Merge state into context field
    const context = {
      ...state.context,
      canvasArtifacts: state.canvasArtifacts,
      phase: state.phase,
      phaseReadiness: state.phaseReadiness,
    }

    await this.update(id, {
      context,
      status: state.status,
    })
  },
}

/**
 * Messages persistence layer
 */
export const messagesApi = {
  /**
   * Get all messages for a project
   */
  async list(projectId: string): Promise<Message[]> {
    const { data, error } = await supabase
      .from('messages')
      .select('*')
      .eq('project_id', projectId)
      .order('created_at', { ascending: true })

    if (error) throw error

    return data.map((msg) => ({
      id: msg.id,
      role: msg.role as 'user' | 'ai',
      content: msg.content,
      timestamp: new Date(msg.created_at).getTime(),
    }))
  },

  /**
   * Add a new message
   */
  async create(
    projectId: string,
    role: 'user' | 'ai',
    content: string,
    metadata: Record<string, unknown> = {}
  ): Promise<Message> {
    const { data, error } = await supabase
      .from('messages')
      .insert({
        project_id: projectId,
        role,
        content,
        metadata,
      })
      .select()
      .single()

    if (error) throw error

    return {
      id: data.id,
      role: data.role as 'user' | 'ai',
      content: data.content,
      timestamp: new Date(data.created_at).getTime(),
    }
  },

  /**
   * Delete all messages for a project
   */
  async deleteAll(projectId: string): Promise<void> {
    const { error } = await supabase
      .from('messages')
      .delete()
      .eq('project_id', projectId)

    if (error) throw error
  },
}

/**
 * Design versions persistence layer
 */
export const designVersionsApi = {
  /**
   * Get all design versions for a project
   */
  async list(projectId: string): Promise<DesignVersionRow[]> {
    const { data, error } = await supabase
      .from('design_versions')
      .select('*')
      .eq('project_id', projectId)
      .order('version_number', { ascending: false })

    if (error) throw error
    return data
  },

  /**
   * Add a new design version
   */
  async create(
    projectId: string,
    snapshot: unknown,
    action: string,
    userAction: boolean = true
  ): Promise<DesignVersionRow> {
    // Get the latest version number
    const { data: latest } = await supabase
      .from('design_versions')
      .select('version_number')
      .eq('project_id', projectId)
      .order('version_number', { ascending: false })
      .limit(1)
      .single()

    const versionNumber = (latest?.version_number ?? 0) + 1

    const { data, error } = await supabase
      .from('design_versions')
      .insert({
        project_id: projectId,
        version_number: versionNumber,
        snapshot,
        action,
        user_action: userAction,
      })
      .select()
      .single()

    if (error) throw error
    return data
  },

  /**
   * Delete all versions for a project
   */
  async deleteAll(projectId: string): Promise<void> {
    const { error } = await supabase
      .from('design_versions')
      .delete()
      .eq('project_id', projectId)

    if (error) throw error
  },
}
