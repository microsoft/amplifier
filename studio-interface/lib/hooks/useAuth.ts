import { useEffect, useState } from 'react'
import { User, Session, AuthError } from '@supabase/supabase-js'
import { supabase } from '@/lib/supabase'

export interface AuthState {
  user: User | null
  session: Session | null
  loading: boolean
  error: AuthError | null
}

export function useAuth() {
  const [authState, setAuthState] = useState<AuthState>({
    user: null,
    session: null,
    loading: true,
    error: null,
  })

  useEffect(() => {
    // Get initial session
    supabase.auth.getSession().then(({ data: { session }, error }) => {
      setAuthState({
        user: session?.user ?? null,
        session,
        loading: false,
        error,
      })
    })

    // Listen for auth changes
    const {
      data: { subscription },
    } = supabase.auth.onAuthStateChange((_event, session) => {
      setAuthState({
        user: session?.user ?? null,
        session,
        loading: false,
        error: null,
      })
    })

    return () => subscription.unsubscribe()
  }, [])

  const signIn = async (email: string, password: string) => {
    setAuthState((prev) => ({ ...prev, loading: true, error: null }))
    const { data, error } = await supabase.auth.signInWithPassword({
      email,
      password,
    })
    setAuthState((prev) => ({
      user: data.user,
      session: data.session,
      loading: false,
      error,
    }))
    return { data, error }
  }

  const signUp = async (email: string, password: string) => {
    setAuthState((prev) => ({ ...prev, loading: true, error: null }))
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    })
    setAuthState((prev) => ({
      user: data.user,
      session: data.session,
      loading: false,
      error,
    }))
    return { data, error }
  }

  const signInWithMagicLink = async (email: string) => {
    setAuthState((prev) => ({ ...prev, loading: true, error: null }))
    const { data, error } = await supabase.auth.signInWithOtp({
      email,
      options: {
        emailRedirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    setAuthState((prev) => ({
      ...prev,
      loading: false,
      error,
    }))
    return { data, error }
  }

  const signInWithOAuth = async (provider: 'google' | 'github') => {
    setAuthState((prev) => ({ ...prev, loading: true, error: null }))
    const { data, error } = await supabase.auth.signInWithOAuth({
      provider,
      options: {
        redirectTo: `${window.location.origin}/auth/callback`,
      },
    })
    setAuthState((prev) => ({
      ...prev,
      loading: false,
      error,
    }))
    return { data, error }
  }

  const signOut = async () => {
    setAuthState((prev) => ({ ...prev, loading: true }))
    const { error } = await supabase.auth.signOut()
    setAuthState({
      user: null,
      session: null,
      loading: false,
      error,
    })
    return { error }
  }

  return {
    ...authState,
    signIn,
    signUp,
    signInWithMagicLink,
    signInWithOAuth,
    signOut,
  }
}
