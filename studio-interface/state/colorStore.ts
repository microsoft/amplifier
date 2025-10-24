/**
 * ColorStore - Centralized Color State Management
 *
 * A self-contained Zustand store for managing color state with
 * undo/redo, preview capabilities, and real-time CSS synchronization.
 *
 * Contract:
 * - Single source of truth for all color state
 * - Maintains history for undo/redo operations
 * - Supports non-destructive preview of color changes
 * - Integrates with CSSVariableInjector for real-time updates
 *
 * @module ColorStore
 */

import { create } from 'zustand';
import type {
  HSLColor,
  ColorPalette,
  ColorSuggestion,
  ColorChange
} from '../../packages/color-intelligence/types';
// Import color parsing utilities
import { parseCSSColor, resolveCSSVariable } from '../utils/colorParser';

/**
 * Token mapping from ColorPalette keys to CSS variable names
 */
export const TOKEN_MAP: Record<keyof ColorPalette, string> = {
  background: '--background',
  surface: '--surface',
  text: '--text',
  textMuted: '--text-muted',
  border: '--border',
  primary: '--primary',
  accent: '--accent',
  success: '--color-success',
  warning: '--color-attention',
  error: '--color-error',
  info: '--color-info',
};

/**
 * Single change entry in the history stack
 */
export interface ColorHistoryEntry {
  /** Unix timestamp of the change */
  timestamp: number;
  /** Map of token names to color changes */
  changes: Map<string, { from: HSLColor; to: HSLColor }>;
  /** Human-readable description of the change */
  description: string;
}

/**
 * Complete color store state structure
 */
interface ColorStoreState {
  /** Current active color palette */
  colors: ColorPalette;
  /** History stack for undo/redo */
  history: ColorHistoryEntry[];
  /** Current position in history stack */
  historyIndex: number;
  /** Token currently being previewed */
  previewToken: string | null;
  /** Preview color value */
  previewColor: HSLColor | null;
  /** Available color suggestions */
  suggestions: ColorSuggestion[];
  /** Whether store has been initialized from CSS */
  isInitialized: boolean;
}

/**
 * Store actions for color manipulation
 */
interface ColorStoreActions {
  /**
   * Update a color and commit to history
   * @param token - Color token name (e.g., 'background')
   * @param color - New HSL color value
   * @param description - Optional change description for history
   */
  updateColor: (token: keyof ColorPalette, color: HSLColor, description?: string) => void;

  /**
   * Preview a color change without committing
   * @param token - Color token name
   * @param color - Preview HSL color value
   */
  previewColorChange: (token: keyof ColorPalette, color: HSLColor) => void;

  /**
   * Clear any active preview
   */
  clearPreview: () => void;

  /**
   * Revert a specific token to its previous value
   * @param token - Token to revert
   */
  revertColor: (token: keyof ColorPalette) => void;

  /**
   * Undo last color change
   * @returns Whether undo was successful
   */
  undo: () => boolean;

  /**
   * Redo previously undone change
   * @returns Whether redo was successful
   */
  redo: () => boolean;

  /**
   * Apply a suggested color palette
   * @param suggestionId - ID of suggestion to apply
   */
  applySuggestion: (suggestionId: string) => void;

  /**
   * Update available suggestions
   * @param suggestions - New suggestions array
   */
  setSuggestions: (suggestions: ColorSuggestion[]) => void;

  /**
   * Initialize store from current CSS variables
   */
  initializeFromCSS: () => void;

  /**
   * Batch update multiple colors as single transaction
   * @param changes - Array of color changes
   * @param description - Description for history entry
   */
  batchUpdateColors: (
    changes: Array<{ token: keyof ColorPalette; color: HSLColor }>,
    description: string
  ) => void;

  /**
   * Get the current effective color (considering preview)
   * @param token - Token to get color for
   * @returns Current or preview color
   */
  getEffectiveColor: (token: keyof ColorPalette) => HSLColor;

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
export type ColorStore = ColorStoreState & ColorStoreActions;

/**
 * Version number for the color palette schema
 * Increment this when DEFAULT_PALETTE changes to invalidate old localStorage cache
 */
const PALETTE_VERSION = 2; // Incremented to fix green background bug

/**
 * Default color palette - Swedish design aesthetic
 * Note: s and l values are decimals (0-1), not percentages
 * These should match the light theme values in globals.css
 */
const DEFAULT_PALETTE: ColorPalette = {
  background: { h: 240, s: 1.0, l: 0.99 },  // #FAFAFF - ghost white
  surface: { h: 220, s: 0.15, l: 0.94 },    // #EEF0F2 - anti-flash-white
  text: { h: 0, s: 0, l: 0.11 },            // #1C1C1C - eerie black
  textMuted: { h: 0, s: 0, l: 0.42 },       // #6B6B6B
  border: { h: 60, s: 0.08, l: 0.85 },      // #DADDD8 - platinum
  primary: { h: 217, s: 0.90, l: 0.60 },    // hsl(217, 90%, 60%)
  accent: { h: 270, s: 0.60, l: 0.65 },     // hsl(270, 60%, 65%)
  success: { h: 142, s: 0.70, l: 0.45 },    // hsl(142, 70%, 45%)
  warning: { h: 38, s: 0.90, l: 0.50 },     // hsl(38, 90%, 50%)
  error: { h: 0, s: 0.70, l: 0.50 },        // hsl(0, 70%, 50%)
  info: { h: 200, s: 0.55, l: 0.45 },       // hsl(200, 55%, 45%)
};

/**
 * Main color store using Zustand
 */
export const useColorStore = create<ColorStore>((set, get) => ({
  // Initial state
  colors: DEFAULT_PALETTE,
  history: [],
  historyIndex: -1,
  previewToken: null,
  previewColor: null,
  suggestions: [],
  isInitialized: false,

  // Actions
  updateColor: (token, color, description) => {
    const state = get();
    const oldColor = state.colors[token];

    // Don't update if color hasn't changed
    if (JSON.stringify(oldColor) === JSON.stringify(color)) return;

    // Create history entry
    const historyEntry: ColorHistoryEntry = {
      timestamp: Date.now(),
      changes: new Map([[token, { from: oldColor, to: color }]]),
      description: description || `Changed ${token} color`
    };

    // Truncate history if we're not at the end (user has undone)
    const newHistory = state.history.slice(0, state.historyIndex + 1);
    newHistory.push(historyEntry);

    // Update state
    set({
      colors: { ...state.colors, [token]: color },
      history: newHistory,
      historyIndex: newHistory.length - 1,
      previewToken: null,
      previewColor: null
    });

    // Apply to CSS (will be done via integration)
    if (typeof window !== 'undefined') {
      // Dynamic import to avoid SSR issues
      import('../utils/cssInjector').then(({ injectVariables }) => {
        injectVariables([{ token: TOKEN_MAP[token], value: color }]);
      });
    }

    // Persist to localStorage
    if (typeof window !== 'undefined') {
      localStorage.setItem('colorPalette', JSON.stringify(get().colors));
      localStorage.setItem('colorPaletteVersion', PALETTE_VERSION.toString());
    }
  },

  previewColorChange: (token, color) => {
    set({
      previewToken: token,
      previewColor: color
    });

    // Apply preview to CSS
    if (typeof window !== 'undefined') {
      import('../utils/cssInjector').then(({ previewVariables }) => {
        previewVariables([{ token: TOKEN_MAP[token], value: color }]);
      });
    }
  },

  clearPreview: () => {
    set({
      previewToken: null,
      previewColor: null
    });

    // Revert CSS preview
    if (typeof window !== 'undefined') {
      import('../utils/cssInjector').then(({ revertPreview }) => {
        revertPreview();
      });
    }
  },

  revertColor: (token) => {
    const state = get();

    // Find last change for this token in history
    for (let i = state.historyIndex; i >= 0; i--) {
      const entry = state.history[i];
      const change = entry.changes.get(token);
      if (change) {
        // Revert to 'from' value
        get().updateColor(token, change.from, `Reverted ${token} color`);
        return;
      }
    }
  },

  undo: () => {
    const state = get();
    if (state.historyIndex < 0) return false;

    const entry = state.history[state.historyIndex];
    const newColors = { ...state.colors };

    // Revert all changes in this entry
    entry.changes.forEach((change, token) => {
      newColors[token as keyof ColorPalette] = change.from;
    });

    set({
      colors: newColors,
      historyIndex: state.historyIndex - 1
    });

    // Apply to CSS
    if (typeof window !== 'undefined') {
      import('../utils/cssInjector').then(({ injectVariables }) => {
        const updates = Array.from(entry.changes.entries()).map(([token, change]) => ({
          token: TOKEN_MAP[token as keyof ColorPalette],
          value: change.from
        }));
        updates.forEach(update => injectVariables([update]));
      });
    }

    return true;
  },

  redo: () => {
    const state = get();
    if (state.historyIndex >= state.history.length - 1) return false;

    const entry = state.history[state.historyIndex + 1];
    const newColors = { ...state.colors };

    // Apply all changes in this entry
    entry.changes.forEach((change, token) => {
      newColors[token as keyof ColorPalette] = change.to;
    });

    set({
      colors: newColors,
      historyIndex: state.historyIndex + 1
    });

    // Apply to CSS
    if (typeof window !== 'undefined') {
      import('../utils/cssInjector').then(({ injectVariables }) => {
        const updates = Array.from(entry.changes.entries()).map(([token, change]) => ({
          token: TOKEN_MAP[token as keyof ColorPalette],
          value: change.to
        }));
        updates.forEach(update => injectVariables([update]));
      });
    }

    return true;
  },

  applySuggestion: (suggestionId) => {
    const state = get();
    const suggestion = state.suggestions.find(s => s.id === suggestionId);
    if (!suggestion) return;

    // Apply all changes from suggestion as single transaction
    const changes = suggestion.changes.map(change => ({
      token: change.token as keyof ColorPalette,
      color: change.to
    }));

    get().batchUpdateColors(changes, suggestion.name);

    // Clear suggestions after applying
    set({ suggestions: [] });
  },

  setSuggestions: (suggestions) => {
    set({ suggestions });
  },

  initializeFromCSS: () => {
    if (typeof window === 'undefined') return;

    // Check version and clear old cache if needed
    const savedVersion = localStorage.getItem('colorPaletteVersion');
    const currentVersion = PALETTE_VERSION.toString();

    if (savedVersion !== currentVersion) {
      // Version mismatch - clear old cache
      localStorage.removeItem('colorPalette');
      localStorage.setItem('colorPaletteVersion', currentVersion);
      console.log(`Color palette cache cleared (v${savedVersion || '1'} → v${currentVersion})`);
    }

    // Try to load from localStorage first (user customizations)
    const savedPalette = localStorage.getItem('colorPalette');
    if (savedPalette) {
      try {
        const parsed = JSON.parse(savedPalette);
        set({
          colors: { ...DEFAULT_PALETTE, ...parsed },
          isInitialized: true
        });
        return;
      } catch (e) {
        console.warn('Failed to parse saved color palette', e);
      }
    }

    // Read actual CSS values from the document
    const newColors: Partial<ColorPalette> = {};

    Object.entries(TOKEN_MAP).forEach(([paletteKey, cssVar]) => {
      const cssValue = resolveCSSVariable(cssVar);
      if (cssValue) {
        const hslColor = parseCSSColor(cssValue);
        if (hslColor) {
          newColors[paletteKey as keyof ColorPalette] = hslColor;
        }
      }
    });

    // Use CSS values if found, otherwise defaults
    const finalColors = Object.keys(newColors).length > 0
      ? { ...DEFAULT_PALETTE, ...newColors }
      : DEFAULT_PALETTE;

    set({
      colors: finalColors as ColorPalette,
      isInitialized: true
    });
  },

  batchUpdateColors: (changes, description) => {
    const state = get();
    const changeMap = new Map<string, { from: HSLColor; to: HSLColor }>();
    const newColors = { ...state.colors };

    // Build change map and update colors
    changes.forEach(({ token, color }) => {
      const oldColor = state.colors[token];
      if (JSON.stringify(oldColor) !== JSON.stringify(color)) {
        changeMap.set(token, { from: oldColor, to: color });
        newColors[token] = color;
      }
    });

    // Skip if no actual changes
    if (changeMap.size === 0) return;

    // Create history entry
    const historyEntry: ColorHistoryEntry = {
      timestamp: Date.now(),
      changes: changeMap,
      description
    };

    // Truncate history if needed and add new entry
    const newHistory = state.history.slice(0, state.historyIndex + 1);
    newHistory.push(historyEntry);

    set({
      colors: newColors,
      history: newHistory,
      historyIndex: newHistory.length - 1,
      previewToken: null,
      previewColor: null
    });

    // Apply all changes to CSS
    if (typeof window !== 'undefined') {
      import('../utils/cssInjector').then(({ injectVariables }) => {
        changes.forEach(({ token, color }) => {
          injectVariables([{ token: TOKEN_MAP[token], value: color }]);
        });
      });

      // Persist to localStorage
      localStorage.setItem('colorPalette', JSON.stringify(newColors));
      localStorage.setItem('colorPaletteVersion', PALETTE_VERSION.toString());
    }
  },

  getEffectiveColor: (token) => {
    const state = get();
    if (state.previewToken === token && state.previewColor) {
      return state.previewColor;
    }
    return state.colors[token];
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
 * Wait for DOM to be fully ready before reading CSS variables
 */
if (typeof window !== 'undefined') {
  // Use DOMContentLoaded to ensure CSS is loaded
  const initStore = () => {
    const state = useColorStore.getState();
    if (!state.isInitialized) {
      state.initializeFromCSS();
    }
  };

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initStore);
  } else {
    // DOM is already ready, but use setTimeout to ensure CSS variables are computed
    setTimeout(initStore, 0);
  }
}