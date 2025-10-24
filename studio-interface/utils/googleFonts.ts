/**
 * Google Fonts Integration
 *
 * Purpose: Fetch and manage Google Fonts library for typography system
 * Provides curated selection of high-quality fonts with dynamic loading
 */

export interface GoogleFont {
  family: string;
  category: 'sans-serif' | 'serif' | 'display' | 'handwriting' | 'monospace';
  variants: string[];
  subsets: string[];
  popularity: number; // Ranking on Google Fonts
}

/**
 * Curated selection of Google Fonts
 * Top fonts by category for design system use
 */
export const CURATED_GOOGLE_FONTS: GoogleFont[] = [
  // Sans-Serif (modern, clean)
  { family: 'Inter', category: 'sans-serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 1 },
  { family: 'Roboto', category: 'sans-serif', variants: ['300', '400', '500', '700'], subsets: ['latin'], popularity: 2 },
  { family: 'Open Sans', category: 'sans-serif', variants: ['300', '400', '600', '700'], subsets: ['latin'], popularity: 3 },
  { family: 'Montserrat', category: 'sans-serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 4 },
  { family: 'Poppins', category: 'sans-serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 5 },
  { family: 'Lato', category: 'sans-serif', variants: ['300', '400', '700'], subsets: ['latin'], popularity: 6 },
  { family: 'Raleway', category: 'sans-serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 7 },
  { family: 'Work Sans', category: 'sans-serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 8 },
  { family: 'DM Sans', category: 'sans-serif', variants: ['400', '500', '700'], subsets: ['latin'], popularity: 9 },
  { family: 'Nunito', category: 'sans-serif', variants: ['300', '400', '600', '700'], subsets: ['latin'], popularity: 10 },
  { family: 'Manrope', category: 'sans-serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 11 },
  { family: 'Plus Jakarta Sans', category: 'sans-serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 12 },
  { family: 'Space Grotesk', category: 'sans-serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 13 },

  // Serif (elegant, editorial)
  { family: 'Playfair Display', category: 'serif', variants: ['400', '500', '600', '700'], subsets: ['latin'], popularity: 14 },
  { family: 'Merriweather', category: 'serif', variants: ['300', '400', '700'], subsets: ['latin'], popularity: 15 },
  { family: 'Lora', category: 'serif', variants: ['400', '500', '600', '700'], subsets: ['latin'], popularity: 16 },
  { family: 'Crimson Text', category: 'serif', variants: ['400', '600', '700'], subsets: ['latin'], popularity: 17 },
  { family: 'EB Garamond', category: 'serif', variants: ['400', '500', '600', '700'], subsets: ['latin'], popularity: 18 },
  { family: 'Cormorant', category: 'serif', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 19 },
  { family: 'Libre Baskerville', category: 'serif', variants: ['400', '700'], subsets: ['latin'], popularity: 20 },
  { family: 'Source Serif Pro', category: 'serif', variants: ['300', '400', '600', '700'], subsets: ['latin'], popularity: 21 },

  // Display (distinctive, headings)
  { family: 'Bebas Neue', category: 'display', variants: ['400'], subsets: ['latin'], popularity: 22 },
  { family: 'Righteous', category: 'display', variants: ['400'], subsets: ['latin'], popularity: 23 },
  { family: 'Outfit', category: 'display', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 24 },
  { family: 'Archivo Black', category: 'display', variants: ['400'], subsets: ['latin'], popularity: 25 },
  { family: 'Syne', category: 'display', variants: ['400', '500', '600', '700'], subsets: ['latin'], popularity: 26 },

  // Monospace (code, technical)
  { family: 'Fira Code', category: 'monospace', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 27 },
  { family: 'JetBrains Mono', category: 'monospace', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 28 },
  { family: 'IBM Plex Mono', category: 'monospace', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 29 },
  { family: 'Source Code Pro', category: 'monospace', variants: ['300', '400', '500', '600', '700'], subsets: ['latin'], popularity: 30 },
  { family: 'Roboto Mono', category: 'monospace', variants: ['300', '400', '500', '700'], subsets: ['latin'], popularity: 31 },
  { family: 'Space Mono', category: 'monospace', variants: ['400', '700'], subsets: ['latin'], popularity: 32 },
  { family: 'Inconsolata', category: 'monospace', variants: ['300', '400', '500', '700'], subsets: ['latin'], popularity: 33 },
];

/**
 * Load Google Font dynamically
 * Injects <link> tag into document head
 */
export function loadGoogleFont(family: string, weights: string[] = ['400']): void {
  const fontId = `google-font-${family.replace(/\s+/g, '-').toLowerCase()}`;

  // Check if already loaded
  if (document.getElementById(fontId)) {
    return;
  }

  // Build font URL
  const weightsParam = weights.join(';');
  const fontUrl = `https://fonts.googleapis.com/css2?family=${encodeURIComponent(family)}:wght@${weightsParam}&display=swap`;

  // Create and inject link tag
  const link = document.createElement('link');
  link.id = fontId;
  link.rel = 'stylesheet';
  link.href = fontUrl;
  document.head.appendChild(link);
}

/**
 * Unload Google Font
 * Removes <link> tag from document head
 */
export function unloadGoogleFont(family: string): void {
  const fontId = `google-font-${family.replace(/\s+/g, '-').toLowerCase()}`;
  const link = document.getElementById(fontId);
  if (link) {
    link.remove();
  }
}

/**
 * Get font CSS family string
 */
export function getFontFamily(family: string, category: GoogleFont['category']): string {
  const fallbacks = {
    'sans-serif': 'system-ui, sans-serif',
    'serif': 'Georgia, serif',
    'monospace': 'ui-monospace, monospace',
    'display': 'system-ui, sans-serif',
    'handwriting': 'cursive'
  };

  return `'${family}', ${fallbacks[category]}`;
}

/**
 * Filter fonts by category
 */
export function getFontsByCategory(category: GoogleFont['category']): GoogleFont[] {
  return CURATED_GOOGLE_FONTS.filter(font => font.category === category);
}

/**
 * Search fonts by name
 */
export function searchFonts(query: string): GoogleFont[] {
  const lowerQuery = query.toLowerCase();
  return CURATED_GOOGLE_FONTS.filter(font =>
    font.family.toLowerCase().includes(lowerQuery)
  );
}

/**
 * Get appropriate categories for font token
 */
export function getCategoriesForToken(token: 'heading' | 'body' | 'mono'): GoogleFont['category'][] {
  switch (token) {
    case 'heading':
      return ['sans-serif', 'serif', 'display'];
    case 'body':
      return ['sans-serif', 'serif'];
    case 'mono':
      return ['monospace'];
    default:
      return ['sans-serif'];
  }
}
