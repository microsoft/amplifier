/**
 * Studio Design Tokens - Typography
 * Clear hierarchy with 1.5× scale ratio
 */

export const typography = {
  // Font families
  fonts: {
    heading: "'Sora', sans-serif",
    body: "'Geist', sans-serif",
    code: "'Source Code Pro', monospace",
  },

  // 1.5× scale for clear hierarchy
  scale: {
    xs: '0.75rem',    // 12px
    sm: '0.875rem',   // 14px
    base: '1rem',     // 16px
    lg: '1.5rem',     // 24px (1.5×)
    xl: '2.25rem',    // 36px (1.5×)
    '2xl': '3.375rem', // 54px (1.5×)
  },

  // Font weights
  weights: {
    regular: 400,
    medium: 500,
    semibold: 600,
    bold: 700,
  },

  // Line heights
  leading: {
    tight: 1.2,
    normal: 1.5,
    relaxed: 1.75,
  },

  // Letter spacing
  tracking: {
    tight: '-0.02em',
    normal: '0',
    wide: '0.02em',
  }
} as const

export type Typography = typeof typography
