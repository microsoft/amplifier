'use client'

import { ComponentShowcase } from '@/components/ComponentShowcase'

/**
 * Design System Page
 *
 * Direct access to the ComponentShowcase for design system development and testing.
 * Accessible at: /designsystem
 *
 * Shows all UI components, tokens, and patterns in one place.
 */
export default function DesignSystemPage() {
  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: 'var(--background)',
      overflow: 'hidden'
    }}>
      <ComponentShowcase />
    </div>
  )
}
