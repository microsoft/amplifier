/**
 * Studio Design Tokens - Colors
 * Foundation palette for "German car facility" aesthetic
 */

export const colors = {
  // Foundation - Light Mode
  foundation: {
    ghostWhite: '#FAFAFF',      // Background
    antiFlashWhite: '#EEF0F2',  // Clean white surfaces
    alabaster: '#ECEBE4',        // Warm light gray
    platinum: '#DADDD8',         // Warm mid gray
    eerieBlack: '#1C1C1C',       // Darkest elements
  },

  // Functional - AI States
  ai: {
    thinking: 'hsl(217, 90%, 60%)',  // Pulsing blue (deliberate timing)
    message: 'hsl(270, 60%, 65%)',   // Purple (AI voice)
  },

  // Functional - User States
  user: {
    message: 'hsl(217, 90%, 60%)',   // Blue (user voice)
  },

  // Functional - Feedback
  feedback: {
    success: 'hsl(142, 70%, 45%)',   // Green
    attention: 'hsl(38, 90%, 50%)',  // Amber
    error: 'hsl(0, 70%, 50%)',       // Red
  },

  // Semantic - For easy reference
  semantic: {
    background: '#FAFAFF',
    surface: '#EEF0F2',
    surfaceWarm: '#ECEBE4',
    border: '#DADDD8',
    text: '#1C1C1C',
    textMuted: '#DADDD8',
  }
} as const

export type Colors = typeof colors
