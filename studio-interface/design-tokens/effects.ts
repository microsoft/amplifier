/**
 * Studio Design Tokens - Effects
 * Frosted glass aesthetic + subtle shadows
 */

export const effects = {
  // Frosted glass/backdrop blur
  frosted: {
    panel: {
      backdropFilter: 'blur(12px)',
      background: 'rgba(255, 255, 255, 0.8)',
      border: '1px solid rgba(255, 255, 255, 0.2)',
    },

    modal: {
      backdropFilter: 'blur(16px)',
      background: 'rgba(255, 255, 255, 0.9)',
      border: '1px solid rgba(255, 255, 255, 0.3)',
    },

    sidebar: {
      backdropFilter: 'blur(10px)',
      background: 'rgba(250, 250, 255, 0.75)',
      border: '1px solid rgba(218, 221, 216, 0.3)',
    }
  },

  // Shadows - subtle elevation
  shadows: {
    subtle: '0 1px 3px rgba(0, 0, 0, 0.05)',
    panel: '0 4px 6px rgba(0, 0, 0, 0.07)',
    elevated: '0 10px 15px rgba(0, 0, 0, 0.1)',
    focus: '0 0 0 3px rgba(28, 28, 28, 0.1)',
  },

  // Border radius
  radius: {
    sm: '4px',
    md: '8px',
    lg: '12px',
    xl: '16px',
    full: '9999px',
  }
} as const

export type Effects = typeof effects
