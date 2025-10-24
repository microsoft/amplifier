/**
 * TypographyStore - Centralized Typography State Management
 *
 * A self-contained Zustand store for managing font selections with
 * undo/redo, preview capabilities, and real-time CSS synchronization.
 *
 * Contract:
 * - Single source of truth for all typography state
 * - Maintains history for undo/redo operations
 * - Supports non-destructive preview of font changes
 * - Integrates with CSS variable injection for real-time updates
 *
 * @module TypographyStore
 */

import { create } from 'zustand';

/**
 * Font configuration for a single role
 */
export interface FontConfig {
  /** Font family CSS value */
  family: string;
  /** Font weights available */
  weights: number[];
  /** Line height multiplier */
  lineHeight?: number;
  /** Letter spacing */
  letterSpacing?: string;
}

/**
 * Complete typography palette
 */
export interface TypographyPalette {
  heading: string;
  body: string;
  mono: string;
}

/**
 * Token mapping from palette keys to CSS variable names
 * Note: These map to the actual CSS variables used throughout the UI
 */
export const FONT_TOKEN_MAP: Record<keyof TypographyPalette, string> = {
  heading: '--font-sora', // Used in h1-h6, .font-heading
  body: '--font-geist-sans', // Used in body, p, .font-body
  mono: '--font-geist-mono' // Used in code, pre, .font-code
};

/**
 * Single change entry in the history stack
 */
export interface FontHistoryEntry {
  /** Unix timestamp of the change */
  timestamp: number;
  /** Map of token names to font changes */
  changes: Map<string, { from: string; to: string }>;
  /** Human-readable description of the change */
  description: string;
}

/**
 * Complete typography store state structure
 */
interface TypographyStoreState {
  /** Current active font palette */
  fonts: TypographyPalette;
  /** History stack for undo/redo */
  history: FontHistoryEntry[];
  /** Current position in history stack */
  historyIndex: number;
  /** Token currently being previewed */
  previewToken: string | null;
  /** Preview font value */
  previewFont: string | null;
  /** Whether store has been initialized from CSS */
  isInitialized: boolean;
}

/**
 * Store actions for typography manipulation
 */
interface TypographyStoreActions {
  /**
   * Update a font and commit to history
   * @param token - Font token name (e.g., 'heading')
   * @param font - New font family value
   * @param description - Optional change description for history
   */
  updateFont: (token: keyof TypographyPalette, font: string, description?: string) => void;

  /**
   * Preview a font change without committing
   * @param token - Font token name
   * @param font - Preview font family value
   */
  previewFontChange: (token: keyof TypographyPalette, font: string) => void;

  /**
   * Clear any active preview
   */
  clearPreview: () => void;

  /**
   * Revert a specific token to its previous value
   * @param token - Token to revert
   */
  revertFont: (token: keyof TypographyPalette) => void;

  /**
   * Undo last font change
   * @returns Whether undo was successful
   */
  undo: () => boolean;

  /**
   * Redo previously undone change
   * @returns Whether redo was successful
   */
  redo: () => boolean;

  /**
   * Initialize store from current CSS variables
   */
  initializeFromCSS: () => void;

  /**
   * Batch update multiple fonts as single transaction
   * @param changes - Array of font changes
   * @param description - Description for history entry
   */
  batchUpdateFonts: (
    changes: Array<{ token: keyof TypographyPalette; font: string }>,
    description: string
  ) => void;

  /**
   * Get the current effective font (considering preview)
   * @param token - Token to get font for
   * @returns Current or preview font
   */
  getEffectiveFont: (token: keyof TypographyPalette) => string;

  /**
   * Check if we can undo
   */
  canUndo: () => boolean;

  /**
   * Check if we can redo
   */
  canRedo: () => boolean;
}

/**
 * Combined store type
 */
export type TypographyStore = TypographyStoreState & TypographyStoreActions;

/**
 * Default typography palette - Studio defaults
 * These should match the font values from Next.js font loader
 */
const DEFAULT_PALETTE: TypographyPalette = {
  heading: "'Sora', system-ui, sans-serif",
  body: "'Geist', system-ui, sans-serif",
  mono: "'Geist Mono', ui-monospace, monospace"
};

/**
 * Inject font family into CSS variables
 */
function injectFontVariable(token: string, fontFamily: string): void {
  if (typeof window === 'undefined') return;

  requestAnimationFrame(() => {
    const root = document.documentElement;
    root.style.setProperty(token, fontFamily);
  });
}

/**
 * Parse CSS font-family value to clean format
 */
function parseFontFamily(cssValue: string): string {
  // Remove extra quotes and clean up
  return cssValue.trim();
}

/**
 * Main typography store using Zustand
 */
export const useTypographyStore = create<TypographyStore>((set, get) => ({
  // Initial state
  fonts: DEFAULT_PALETTE,
  history: [],
  historyIndex: -1,
  previewToken: null,
  previewFont: null,
  isInitialized: false,

  // Actions
  updateFont: (token, font, description) => {
    const state = get();
    const oldFont = state.fonts[token];

    // Don't update if font hasn't changed
    if (oldFont === font) return;

    // Create history entry
    const historyEntry: FontHistoryEntry = {
      timestamp: Date.now(),
      changes: new Map([[token, { from: oldFont, to: font }]]),
      description: description || `Changed ${token} font`
    };

    // Truncate history if we're not at the end (user has undone)
    const newHistory = state.history.slice(0, state.historyIndex + 1);
    newHistory.push(historyEntry);

    // Update state
    set({
      fonts: { ...state.fonts, [token]: font },
      history: newHistory,
      historyIndex: newHistory.length - 1,
      previewToken: null,
      previewFont: null
    });

    // Apply to CSS
    injectFontVariable(FONT_TOKEN_MAP[token], font);

    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('typographyPalette', JSON.stringify(get().fonts));
    }
  },

  previewFontChange: (token, font) => {
    set({
      previewToken: token,
      previewFont: font
    });

    // Apply preview to CSS
    injectFontVariable(FONT_TOKEN_MAP[token], font);
  },

  clearPreview: () => {
    const state = get();
    set({
      previewToken: null,
      previewFont: null
    });

    // Revert to actual value
    if (state.previewToken) {
      const actualFont = state.fonts[state.previewToken as keyof TypographyPalette];
      injectFontVariable(FONT_TOKEN_MAP[state.previewToken as keyof TypographyPalette], actualFont);
    }
  },

  revertFont: (token) => {
    const state = get();

    // Find last change for this token in history
    for (let i = state.historyIndex; i >= 0; i--) {
      const entry = state.history[i];
      const change = entry.changes.get(token);
      if (change) {
        // Revert to 'from' value
        get().updateFont(token, change.from, `Reverted ${token} font`);
        return;
      }
    }
  },

  undo: () => {
    const state = get();
    if (state.historyIndex < 0) return false;

    const entry = state.history[state.historyIndex];
    const newFonts = { ...state.fonts };

    // Revert all changes in this entry
    entry.changes.forEach((change, token) => {
      newFonts[token as keyof TypographyPalette] = change.from;
    });

    set({
      fonts: newFonts,
      historyIndex: state.historyIndex - 1
    });

    // Apply to CSS
    entry.changes.forEach((change, token) => {
      injectFontVariable(FONT_TOKEN_MAP[token as keyof TypographyPalette], change.from);
    });

    return true;
  },

  redo: () => {
    const state = get();
    if (state.historyIndex >= state.history.length - 1) return false;

    const entry = state.history[state.historyIndex + 1];
    const newFonts = { ...state.fonts };

    // Apply all changes in this entry
    entry.changes.forEach((change, token) => {
      newFonts[token as keyof TypographyPalette] = change.to;
    });

    set({
      fonts: newFonts,
      historyIndex: state.historyIndex + 1
    });

    // Apply to CSS
    entry.changes.forEach((change, token) => {
      injectFontVariable(FONT_TOKEN_MAP[token as keyof TypographyPalette], change.to);
    });

    return true;
  },

  initializeFromCSS: () => {
    if (typeof window === 'undefined') return;

    const computedStyle = getComputedStyle(document.documentElement);
    const newFonts: Partial<TypographyPalette> = {};

    // Try to load from localStorage first
    const savedPalette = localStorage.getItem('typographyPalette');
    if (savedPalette) {
      try {
        const parsed = JSON.parse(savedPalette);
        set({
          fonts: { ...DEFAULT_PALETTE, ...parsed },
          isInitialized: true
        });
        return;
      } catch (e) {
        console.warn('Failed to parse saved typography palette', e);
      }
    }

    // Since Next.js injects font classes as CSS variables with internal class names,
    // we'll just use the defaults which match what we expect the fonts to be
    // The actual font CSS variables contain values like "__Sora_123abc" which aren't useful
    set({
      fonts: DEFAULT_PALETTE,
      isInitialized: true
    });
  },

  batchUpdateFonts: (changes, description) => {
    const state = get();
    const changeMap = new Map<string, { from: string; to: string }>();
    const newFonts = { ...state.fonts };

    // Build change map and update fonts
    changes.forEach(({ token, font }) => {
      const oldFont = state.fonts[token];
      if (oldFont !== font) {
        changeMap.set(token, { from: oldFont, to: font });
        newFonts[token] = font;
      }
    });

    // Skip if no actual changes
    if (changeMap.size === 0) return;

    // Create history entry
    const historyEntry: FontHistoryEntry = {
      timestamp: Date.now(),
      changes: changeMap,
      description
    };

    // Truncate history if needed and add new entry
    const newHistory = state.history.slice(0, state.historyIndex + 1);
    newHistory.push(historyEntry);

    set({
      fonts: newFonts,
      history: newHistory,
      historyIndex: newHistory.length - 1,
      previewToken: null,
      previewFont: null
    });

    // Apply all changes to CSS
    changes.forEach(({ token, font }) => {
      injectFontVariable(FONT_TOKEN_MAP[token], font);
    });

    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('typographyPalette', JSON.stringify(newFonts));
    }
  },

  getEffectiveFont: (token) => {
    const state = get();
    if (state.previewToken === token && state.previewFont) {
      return state.previewFont;
    }
    return state.fonts[token];
  },

  canUndo: () => {
    return get().historyIndex >= 0;
  },

  canRedo: () => {
    const state = get();
    return state.historyIndex < state.history.length - 1;
  }
}));

/**
 * Initialize the store on mount (for client-side only)
 * Wait for DOM to be fully ready
 */
if (typeof window !== 'undefined') {
  // Use DOMContentLoaded to ensure fonts are loaded
  const initStore = () => {
    const state = useTypographyStore.getState();
    if (!state.isInitialized) {
      state.initializeFromCSS();
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStore);
  } else {
    // DOM is already ready
    setTimeout(initStore, 0);
  }
}
