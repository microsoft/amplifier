'use client'

import { useEffect } from 'react'
import { useStudioStore } from '@/state/store'

/**
 * Theme Provider
 * Applies theme to document root and syncs with localStorage
 *
 * Three-tier theme system:
 * - auto: Uses system preference via @media (prefers-color-scheme)
 * - light: Force light mode via [data-theme="light"]
 * - dark: Force dark mode via [data-theme="dark"]
 */
export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const theme = useStudioStore((state) => state.theme)

  useEffect(() => {
    // Load theme from localStorage on mount
    const savedTheme = localStorage.getItem('studio-theme') as 'auto' | 'light' | 'dark' | null
    if (savedTheme && savedTheme !== theme) {
      useStudioStore.getState().setTheme(savedTheme)
    }
  }, [])

  useEffect(() => {
    // Apply theme to document root
    const root = document.documentElement

    if (theme === 'auto') {
      // Remove data-theme attribute to use system preference
      root.removeAttribute('data-theme')
    } else {
      // Set data-theme attribute for manual override
      root.setAttribute('data-theme', theme)
    }
  }, [theme])

  return <>{children}</>
}
