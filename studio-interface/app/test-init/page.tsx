'use client'

import { useEffect, useState } from 'react'
import { useColorStore } from '@/state/colorStore'
import { useTypographyStore } from '@/state/typographyStore'

export default function TestInitPage() {
  const [mounted, setMounted] = useState(false)
  const { colors, isInitialized: colorInitialized, initializeFromCSS: initColors } = useColorStore()
  const { fonts, isInitialized: fontInitialized, initializeFromCSS: initFonts } = useTypographyStore()

  useEffect(() => {
    setMounted(true)
    // Force re-initialization for testing
    if (mounted) {
      initColors()
      initFonts()
    }
  }, [mounted, initColors, initFonts])

  if (!mounted) {
    return <div>Loading...</div>
  }

  return (
    <div style={{ padding: '2rem', fontFamily: 'monospace' }}>
      <h1>CSS Variable Initialization Test</h1>

      <h2>Color Store</h2>
      <p>Initialized: {colorInitialized ? 'Yes' : 'No'}</p>
      <h3>Current Values:</h3>
      <pre>{JSON.stringify(colors, null, 2)}</pre>

      <h2>Typography Store</h2>
      <p>Initialized: {fontInitialized ? 'Yes' : 'No'}</p>
      <h3>Current Values:</h3>
      <pre>{JSON.stringify(fonts, null, 2)}</pre>

      <h2>Actual CSS Values (from computed styles):</h2>
      <div id="css-values"></div>

      <script dangerouslySetInnerHTML={{
        __html: `
          document.addEventListener('DOMContentLoaded', () => {
            const computed = getComputedStyle(document.documentElement);
            const values = {
              '--background': computed.getPropertyValue('--background'),
              '--text': computed.getPropertyValue('--text'),
              '--primary': computed.getPropertyValue('--primary'),
              '--font-sora': computed.getPropertyValue('--font-sora'),
              '--font-geist-sans': computed.getPropertyValue('--font-geist-sans'),
            };
            document.getElementById('css-values').innerHTML = '<pre>' + JSON.stringify(values, null, 2) + '</pre>';
          });
        `
      }} />
    </div>
  )
}