'use client'

import { useState, useEffect } from 'react'
import { ColorEditor } from '../../components/color-system/ColorEditor'
import { useColorStore } from '../../state/colorStore'

export default function ColorTestPage() {
  const [mounted, setMounted] = useState(false)
  const { colors, isInitialized, initializeFromCSS } = useColorStore()

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted && !isInitialized) {
      initializeFromCSS()
    }
  }, [mounted, isInitialized, initializeFromCSS])

  const colorDefinitions = [
    { token: 'background' as const, label: 'Background', desc: 'Canvas, page background' },
    { token: 'surface' as const, label: 'Surface', desc: 'Panel backgrounds' },
    { token: 'text' as const, label: 'Text Primary', desc: 'Primary text color' },
    { token: 'primary' as const, label: 'Primary', desc: 'Brand primary' },
    { token: 'accent' as const, label: 'Accent', desc: 'Brand accent' },
  ]

  if (!mounted) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        Loading interactive color system...
      </div>
    )
  }

  if (!isInitialized) {
    return (
      <div style={{ padding: '2rem', textAlign: 'center' }}>
        Initializing color system...
      </div>
    )
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: 'var(--background)',
      color: 'var(--text)',
      padding: '2rem'
    }}>
      <h1 style={{ fontSize: '2rem', marginBottom: '2rem' }}>
        Interactive Color System Test
      </h1>

      {/* Live Editing Banner */}
      <div style={{
        padding: '1rem',
        background: 'rgba(0, 200, 100, 0.1)',
        border: '1px solid rgba(0, 200, 100, 0.3)',
        borderRadius: '8px',
        marginBottom: '2rem'
      }}>
        <div style={{ fontSize: '1.2rem', fontWeight: 600, marginBottom: '0.5rem' }}>
          ✨ Live Color System
        </div>
        <div style={{ fontSize: '0.9rem', opacity: 0.8 }}>
          Click any color to edit. Changes update instantly across the entire interface.
        </div>
      </div>

      {/* Color Editors Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))',
        gap: '1rem'
      }}>
        {colorDefinitions.map(({ token, label, desc }) => (
          <ColorEditor
            key={token}
            colorToken={token}
            currentColor={colors[token]}
            label={label}
            description={desc}
          />
        ))}
      </div>

      {/* Test Elements */}
      <div style={{ marginTop: '3rem' }}>
        <h2 style={{ marginBottom: '1rem' }}>Test Elements</h2>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
          gap: '1rem'
        }}>
          <div style={{
            padding: '1rem',
            background: 'var(--surface)',
            borderRadius: '8px',
            border: '1px solid var(--border)'
          }}>
            <h3 style={{ color: 'var(--primary)' }}>Surface Card</h3>
            <p style={{ color: 'var(--text-muted)' }}>This uses surface background</p>
          </div>

          <div style={{
            padding: '1rem',
            background: 'var(--primary)',
            color: 'white',
            borderRadius: '8px'
          }}>
            <h3>Primary Card</h3>
            <p>This uses primary color</p>
          </div>

          <div style={{
            padding: '1rem',
            background: 'var(--accent)',
            color: 'white',
            borderRadius: '8px'
          }}>
            <h3>Accent Card</h3>
            <p>This uses accent color</p>
          </div>
        </div>
      </div>
    </div>
  )
}