/**
 * Studio Design Tokens - Behaviors
 * Motion timing + interaction patterns
 */

export const behaviors = {
  // Motion timing - communicates weight and intent
  motion: {
    // Instant (<100ms) - UI interactions (tabs, menus)
    instant: {
      duration: '50ms',
      easing: 'linear',
    },

    // Responsive (200-300ms) - Transitions, refinements
    responsive: {
      duration: '250ms',
      easing: 'cubic-bezier(0.4, 0, 0.2, 1)', // ease-in-out
    },

    // Deliberate (400-600ms) - AI generation, emphasizes thoughtfulness
    deliberate: {
      duration: '500ms',
      easing: 'cubic-bezier(0.34, 1.56, 0.64, 1)', // spring
    },
  },

  // Interaction patterns
  interactions: {
    hover: {
      timing: 'instant',
      feedback: 'subtle', // Color change, underline
    },
    click: {
      timing: 'responsive',
      feedback: 'medium', // Scale, shadow
    },
    drag: {
      timing: 'instant',
      feedback: 'strong', // Elevation, cursor change
    },
    focus: {
      timing: 'instant',
      feedback: 'accessible', // Visible outline
    },
  }
} as const

export type Behaviors = typeof behaviors
