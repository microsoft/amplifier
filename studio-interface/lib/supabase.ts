import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!

export const supabase = createClient(supabaseUrl, supabaseAnonKey)

// Database types based on schema
export interface Database {
  public: {
    Tables: {
      projects: {
        Row: {
          id: string
          user_id: string
          name: string
          status: 'discovery' | 'expression' | 'completed'
          context: Record<string, unknown>
          created_at: string
          updated_at: string
        }
        Insert: {
          id?: string
          user_id: string
          name: string
          status?: 'discovery' | 'expression' | 'completed'
          context?: Record<string, unknown>
          created_at?: string
          updated_at?: string
        }
        Update: {
          id?: string
          user_id?: string
          name?: string
          status?: 'discovery' | 'expression' | 'completed'
          context?: Record<string, unknown>
          created_at?: string
          updated_at?: string
        }
      }
      messages: {
        Row: {
          id: string
          project_id: string
          role: 'user' | 'ai'
          content: string
          metadata: Record<string, unknown>
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          role: 'user' | 'ai'
          content: string
          metadata?: Record<string, unknown>
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          role?: 'user' | 'ai'
          content?: string
          metadata?: Record<string, unknown>
          created_at?: string
        }
      }
      design_versions: {
        Row: {
          id: string
          project_id: string
          version_number: number
          snapshot: Record<string, unknown>
          action: string
          user_action: boolean
          created_at: string
        }
        Insert: {
          id?: string
          project_id: string
          version_number: number
          snapshot: Record<string, unknown>
          action: string
          user_action?: boolean
          created_at?: string
        }
        Update: {
          id?: string
          project_id?: string
          version_number?: number
          snapshot?: Record<string, unknown>
          action?: string
          user_action?: boolean
          created_at?: string
        }
      }
    }
  }
}
