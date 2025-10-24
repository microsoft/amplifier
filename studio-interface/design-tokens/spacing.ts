/**
 * Studio Design Tokens - Spacing & Proportion
 * 8px base unit system
 */

export const spacing = {
  // 8px base unit
  base: 8,

  // Scale (in px)
  scale: {
    0: '0',
    1: '4px',    // 0.5 unit
    2: '8px',    // 1 unit
    3: '12px',   // 1.5 units
    4: '16px',   // 2 units
    6: '24px',   // 3 units
    8: '32px',   // 4 units
    12: '48px',  // 6 units
    16: '64px',  // 8 units
    24: '96px',  // 12 units
    32: '128px', // 16 units
  },

  // Touch targets
  touch: {
    min: 48,        // Minimum touch target (48px)
    primary: 52,    // Primary action buttons (52px)
  },

  // Breakpoints (desktop-first)
  breakpoints: {
    mobile: 640,
    tablet: 768,
    desktop: 1024,
    wide: 1280,
  }
} as const

export type Spacing = typeof spacing
