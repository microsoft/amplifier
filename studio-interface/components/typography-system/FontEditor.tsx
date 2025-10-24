'use client'

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useTypographyStore } from '../../state/typographyStore';
import {
  CURATED_GOOGLE_FONTS,
  loadGoogleFont,
  getFontFamily,
  getCategoriesForToken,
  searchFonts,
  type GoogleFont
} from '../../utils/googleFonts';

/**
 * FontEditor - Interactive font selection with live preview
 *
 * Purpose: Enable users to choose and preview fonts from Google Fonts with the same
 * refined aesthetic as ColorEditor. Shows live preview of font changes across the interface.
 *
 * Aesthetic: Precise, confident, luxury font selection experience.
 * Swedish design studio vibe - subtle, refined, purposeful.
 */

interface FontEditorProps {
  /** Font token name (e.g., 'heading', 'body', 'mono') */
  fontToken: 'heading' | 'body' | 'mono';
  /** Current font family */
  currentFont: string;
  /** Display label */
  label: string;
  /** Description of font purpose */
  description: string;
  /** Sample text to preview */
  sampleText?: string;
  /** Optional callback on font change */
  onFontChange?: (font: string) => void;
}

export const FontEditor: React.FC<FontEditorProps> = ({
  fontToken,
  currentFont,
  label,
  description,
  sampleText,
  onFontChange
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [localFont, setLocalFont] = useState(currentFont);
  const [searchQuery, setSearchQuery] = useState('');
  const [hoveredFont, setHoveredFont] = useState<string | null>(null);

  const { fonts, updateFont, previewFontChange } = useTypographyStore();
  const editorRef = useRef<HTMLDivElement>(null);

  // Get default sample text based on token type
  const getDefaultSampleText = () => {
    switch (fontToken) {
      case 'heading':
        return 'Design Intelligence';
      case 'body':
        return 'The quick brown fox jumps over the lazy dog';
      case 'mono':
        return 'const font = "monospace";';
      default:
        return 'Sample Text';
    }
  };

  const displaySampleText = sampleText || getDefaultSampleText();

  // Get appropriate categories for this font token
  const allowedCategories = getCategoriesForToken(fontToken);

  // Filter and search Google Fonts
  const filteredFonts = CURATED_GOOGLE_FONTS.filter(font => {
    const categoryMatch = allowedCategories.includes(font.category);
    const searchMatch = searchQuery === '' ||
      font.family.toLowerCase().includes(searchQuery.toLowerCase());
    return categoryMatch && searchMatch;
  });

  // Load font when hovering or selecting
  const loadFontIfNeeded = useCallback((fontFamily: string) => {
    const font = CURATED_GOOGLE_FONTS.find(f => f.family === fontFamily);
    if (font) {
      loadGoogleFont(font.family, font.variants);
    }
  }, []);

  // Handle font selection (click)
  const handleFontChange = useCallback((fontFamily: string) => {
    loadFontIfNeeded(fontFamily);
    setLocalFont(fontFamily);
    // Note: Don't apply to UI yet - only when user clicks "Apply Changes"
  }, [loadFontIfNeeded]);

  // Preview font on hover (only updates local preview, not entire UI)
  const handleFontHover = useCallback((fontFamily: string | null) => {
    setHoveredFont(fontFamily);
    if (fontFamily) {
      loadFontIfNeeded(fontFamily);
    }
    // Note: Don't apply to UI - only visual feedback in the modal
  }, [loadFontIfNeeded]);

  // Commit changes - Apply to entire UI
  const handleCommit = useCallback(() => {
    // Convert to CSS family format with fallbacks
    const font = CURATED_GOOGLE_FONTS.find(f => f.family === localFont);
    const cssFamily = font ? getFontFamily(font.family, font.category) : localFont;

    // Now apply to entire UI
    updateFont(fontToken, cssFamily);
    setIsOpen(false);
    onFontChange?.(cssFamily);
  }, [fontToken, localFont, updateFont, onFontChange]);

  // Cancel changes
  const handleCancel = useCallback(() => {
    // Revert to current font (no preview needed since we don't preview in UI)
    setLocalFont(currentFont);
    setIsOpen(false);
    setSearchQuery('');
    setHoveredFont(null);
  }, [currentFont]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (editorRef.current && !editorRef.current.contains(e.target as Node)) {
        if (isOpen && localFont !== currentFont) {
          handleCancel();
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, localFont, currentFont, handleCancel]);

  // Handle keyboard shortcuts
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (!isOpen) return;

      if (e.key === 'Escape') {
        handleCancel();
      } else if (e.key === 'Enter' && !e.shiftKey) {
        handleCommit();
      }
    };

    document.addEventListener('keydown', handleKeyDown);
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, handleCancel, handleCommit]);

  // Get font display name from family string
  const getFontDisplayName = (family: string): string => {
    const font = CURATED_GOOGLE_FONTS.find(f => f.family === family || getFontFamily(f.family, f.category) === family);
    return font?.family || family.split(',')[0].replace(/['"]/g, '');
  };

  return (
    <div style={{ position: 'relative' }} ref={editorRef}>
      {/* Collapsed View - Matches ColorEditor 200px grid */}
      <motion.div
        onClick={() => setIsOpen(true)}
        whileHover={{ scale: 1.01 }}
        whileTap={{ scale: 0.99 }}
        style={{
          cursor: 'pointer',
          padding: 'var(--space-3)',
          background: 'var(--bg-secondary)',
          borderRadius: 'var(--radius-md)',
          border: '1px solid var(--border)',
          transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)',
          minWidth: '200px'
        }}
      >
        {/* Font Preview Area - 64px like color swatch */}
        <div
          style={{
            width: '100%',
            height: '64px',
            background: 'var(--background)',
            borderRadius: 'var(--radius-sm)',
            marginBottom: 'var(--space-2)',
            border: '1px solid var(--border)',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            padding: 'var(--space-2)',
            overflow: 'hidden',
            fontFamily: localFont
          }}
          aria-label={`Font preview: ${getFontDisplayName(localFont)}`}
        >
          <div style={{
            fontSize: fontToken === 'heading' ? '20px' : fontToken === 'mono' ? '13px' : '16px',
            textAlign: 'center',
            lineHeight: '1.2'
          }}>
            {fontToken === 'heading' ? 'Aa' : fontToken === 'mono' ? 'Code' : 'Text'}
          </div>
        </div>

        {/* Label */}
        <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
          {label}
        </div>

        {/* Current Font Name */}
        <code style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-family-mono)' }}>
          {getFontDisplayName(localFont)}
        </code>

        {/* Description */}
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 'var(--space-1)', margin: 0 }}>
          {description}
        </p>
      </motion.div>

      {/* Expanded Editor Modal */}
      <AnimatePresence>
        {isOpen && (
          <motion.div
            initial={{ opacity: 0, scale: 0.98, y: -8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            exit={{ opacity: 0, scale: 0.98, y: -8 }}
            transition={{ duration: 0.15, ease: [0.4, 0, 0.2, 1] }}
            style={{
              position: 'absolute',
              top: 0,
              left: 0,
              right: 0,
              minWidth: '400px',
              maxWidth: '500px',
              zIndex: 100,
              background: 'var(--background)',
              borderRadius: 'var(--radius-lg)',
              boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12), 0 2px 8px rgba(0, 0, 0, 0.08)',
              border: '1px solid var(--border)',
              overflow: 'hidden'
            }}
          >
            {/* Header */}
            <div style={{
              padding: 'var(--space-4)',
              borderBottom: '1px solid var(--border)',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }}>
                <div
                  style={{
                    width: '32px',
                    height: '32px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--bg-secondary)',
                    border: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontFamily: localFont,
                    fontSize: '16px',
                    fontWeight: 600
                  }}
                >
                  Aa
                </div>
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px' }}>{label}</div>
                  <code style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-family-mono)' }}>
                    {getFontDisplayName(localFont)}
                  </code>
                </div>
              </div>
              <button
                onClick={handleCancel}
                style={{
                  background: 'transparent',
                  border: 'none',
                  fontSize: '20px',
                  cursor: 'pointer',
                  color: 'var(--text-muted)',
                  transition: 'color 150ms',
                  padding: 'var(--space-2)',
                  lineHeight: 1
                }}
                aria-label="Close font editor"
                onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text)'}
                onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
              >
                ×
              </button>
            </div>

            {/* Live Preview Area */}
            <div style={{
              padding: 'var(--space-6)',
              borderBottom: '1px solid var(--border)',
              background: 'var(--bg-secondary)'
            }}>
              <div style={{
                fontFamily: localFont,
                fontSize: fontToken === 'heading' ? '32px' : fontToken === 'mono' ? '14px' : '18px',
                lineHeight: fontToken === 'heading' ? '1.2' : fontToken === 'mono' ? '1.5' : '1.5',
                fontWeight: fontToken === 'heading' ? 600 : 400,
                color: 'var(--text)',
                textAlign: 'center',
                padding: 'var(--space-4)'
              }}>
                {displaySampleText}
              </div>
              <div style={{
                fontSize: '11px',
                color: 'var(--text-muted)',
                textAlign: 'center',
                marginTop: 'var(--space-2)'
              }}>
                Live preview • Changes update instantly
              </div>
            </div>

            {/* Search */}
            <div style={{ padding: 'var(--space-4) var(--space-6)' }}>
              <input
                type="text"
                placeholder="Search fonts..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                className="studio-input"
                style={{
                  width: '100%',
                  fontSize: '13px',
                  padding: 'var(--space-2) var(--space-3)'
                }}
                autoFocus
              />
            </div>

            {/* Font List */}
            <div style={{
              maxHeight: '320px',
              overflowY: 'auto',
              padding: 'var(--space-2) var(--space-6) var(--space-6)'
            }}>
              {filteredFonts.length === 0 && (
                <div style={{
                  padding: 'var(--space-8)',
                  textAlign: 'center',
                  color: 'var(--text-muted)',
                  fontSize: '13px'
                }}>
                  No fonts found matching "{searchQuery}"
                </div>
              )}

              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
                {filteredFonts.map((font) => {
                  const cssFamily = getFontFamily(font.family, font.category);
                  const isSelected = localFont === font.family || localFont === cssFamily;
                  const isHovered = hoveredFont === font.family;

                  return (
                    <motion.div
                      key={font.family}
                      whileHover={{ scale: 1.005 }}
                      onClick={() => handleFontChange(font.family)}
                      onMouseEnter={() => handleFontHover(font.family)}
                      onMouseLeave={() => handleFontHover(null)}
                      style={{
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-md)',
                        background: isSelected ? 'var(--color-hover)' : 'transparent',
                        border: `1px solid ${isSelected ? 'var(--text-muted)' : 'var(--border)'}`,
                        cursor: 'pointer',
                        transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)'
                      }}
                    >
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                        <div>
                          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
                            {font.family}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'capitalize' }}>
                            {font.category.replace('-', ' ')}
                          </div>
                        </div>
                        {isSelected && (
                          <div style={{
                            width: '16px',
                            height: '16px',
                            borderRadius: '50%',
                            background: 'var(--primary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center'
                          }}>
                            <svg width="10" height="8" viewBox="0 0 10 8" fill="none">
                              <path d="M1 4L3.5 6.5L9 1" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"/>
                            </svg>
                          </div>
                        )}
                      </div>
                      {/* Font Preview */}
                      <div style={{
                        fontFamily: cssFamily,
                        fontSize: fontToken === 'heading' ? '18px' : fontToken === 'mono' ? '13px' : '14px',
                        color: 'var(--text)',
                        padding: 'var(--space-2)',
                        background: 'var(--background)',
                        borderRadius: 'var(--radius-sm)',
                        border: '1px solid var(--border)'
                      }}>
                        {fontToken === 'heading' ? 'The Quick Brown Fox' : displaySampleText}
                      </div>
                    </motion.div>
                  );
                })}
              </div>
            </div>

            {/* Actions */}
            <div style={{
              padding: 'var(--space-4) var(--space-6)',
              borderTop: '1px solid var(--border)',
              display: 'flex',
              justifyContent: 'flex-end',
              gap: 'var(--space-3)',
              background: 'var(--bg-secondary)'
            }}>
              <button
                onClick={handleCancel}
                style={{
                  padding: 'var(--space-2-5) var(--space-4)',
                  borderRadius: 'var(--radius-md)',
                  background: 'transparent',
                  border: '1px solid var(--border)',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 500,
                  color: 'var(--text)',
                  transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.background = 'var(--color-hover)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.background = 'transparent';
                }}
              >
                Cancel
              </button>
              <button
                onClick={handleCommit}
                style={{
                  padding: 'var(--space-2-5) var(--space-6)',
                  borderRadius: 'var(--radius-md)',
                  background: 'var(--primary)',
                  color: 'white',
                  border: 'none',
                  cursor: 'pointer',
                  fontSize: '13px',
                  fontWeight: 600,
                  transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)'
                }}
                onMouseEnter={(e) => {
                  e.currentTarget.style.opacity = '0.9';
                  e.currentTarget.style.transform = 'scale(1.02)';
                }}
                onMouseLeave={(e) => {
                  e.currentTarget.style.opacity = '1';
                  e.currentTarget.style.transform = 'scale(1)';
                }}
              >
                Apply Changes
              </button>
            </div>
          </motion.div>
        )}
      </AnimatePresence>
    </div>
  );
};
