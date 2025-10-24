import React, { useState, useEffect, useCallback, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { useColorStore } from '../../state/colorStore';
import type {
  HSLColor,
  ColorAnalysis,
  ColorSuggestion,
  ColorContext
} from '../../../packages/color-intelligence/types';
import {
  analyzeColor,
  generateSuggestions
} from '../../../packages/color-intelligence';

interface ColorEditorProps {
  colorToken: string; // e.g., 'background', 'text', 'primary'
  currentColor: HSLColor;
  label: string; // Display name
  description: string; // What this color is for
  onColorChange?: (color: HSLColor) => void; // Optional callback
}

interface SliderProps {
  min: number;
  max: number;
  value: number;
  onChange: (value: number) => void;
  label: string;
  unit: string;
  gradient?: string;
}

const Slider: React.FC<SliderProps> = ({
  min,
  max,
  value,
  onChange,
  label,
  unit,
  gradient
}) => {
  const percentage = ((value - min) / (max - min)) * 100;

  return (
    <div style={{ marginBottom: 'var(--space-4)' }}>
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        marginBottom: 'var(--space-2)',
        fontSize: '13px',
        fontWeight: 500
      }}>
        <span>{label}</span>
        <span style={{ color: 'var(--text-muted)', fontFamily: 'var(--font-family-mono)' }}>
          {Math.round(value)}{unit}
        </span>
      </div>
      <div style={{
        position: 'relative',
        height: '32px',
        background: gradient || 'var(--border)',
        borderRadius: 'var(--radius-sm)',
        overflow: 'hidden',
        border: '1px solid var(--border)'
      }}>
        <input
          type="range"
          min={min}
          max={max}
          value={value}
          onChange={(e) => onChange(Number(e.target.value))}
          style={{
            position: 'absolute',
            width: '100%',
            height: '100%',
            opacity: 0,
            cursor: 'pointer',
            zIndex: 2,
            margin: 0
          }}
          aria-label={`${label}: ${Math.round(value)}${unit}`}
        />
        <div style={{
          position: 'absolute',
          width: '16px',
          height: '16px',
          background: 'var(--background)',
          border: '2px solid var(--text)',
          borderRadius: '50%',
          top: '50%',
          left: `${percentage}%`,
          transform: 'translate(-50%, -50%)',
          pointerEvents: 'none',
          boxShadow: '0 2px 4px rgba(0, 0, 0, 0.1)',
          zIndex: 1,
          transition: 'transform 100ms cubic-bezier(0.4, 0, 0.2, 1)'
        }} />
      </div>
    </div>
  );
};

export const ColorEditor: React.FC<ColorEditorProps> = ({
  colorToken,
  currentColor,
  label,
  description,
  onColorChange
}) => {
  const [isOpen, setIsOpen] = useState(false);
  const [localColor, setLocalColor] = useState(currentColor);
  const [suggestions, setSuggestions] = useState<ColorSuggestion[]>([]);
  const [analysis, setAnalysis] = useState<ColorAnalysis | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [selectedSuggestion, setSelectedSuggestion] = useState<string | null>(null);

  const { colors, updateColor, previewColorChange } = useColorStore();
  const editorRef = useRef<HTMLDivElement>(null);
  const debounceTimer = useRef<NodeJS.Timeout>();

  // Determine role from token
  const determineRole = (token: string): 'dominant' | 'accent' | 'supporting' => {
    if (token === 'primary' || token === 'brand') return 'accent';
    if (token === 'background' || token === 'surface') return 'dominant';
    return 'supporting';
  };

  // Handle color change with debounced analysis
  const handleColorChange = useCallback((newColor: HSLColor) => {
    setLocalColor(newColor);

    // Preview in UI immediately (non-destructive)
    previewColorChange(colorToken, newColor);

    // Debounce analysis and suggestions
    if (debounceTimer.current) {
      clearTimeout(debounceTimer.current);
    }

    debounceTimer.current = setTimeout(() => {
      setIsAnalyzing(true);

      // Create context for analysis
      const context: ColorContext = {
        role: determineRole(colorToken),
        appliedTo: [colorToken],
        adjacentColors: Object.entries(colors)
          .filter(([key]) => key !== colorToken)
          .map(([_, color]) => color)
          .slice(0, 3) // Limit to nearby colors
      };

      // Analyze change
      const result = analyzeColor({
        originalColor: currentColor,
        newColor: newColor,
        palette: colors,
        context: context
      });
      setAnalysis(result.analysis);

      // Generate suggestions
      const suggestionResult = generateSuggestions({
        analysis: result.analysis,
        currentPalette: colors,
        intent: {
          goal: 'harmonize',
          magnitude: 'subtle',
        },
        constraints: {
          minimumContrast: 4.5,
          maxSaturation: 0.8,
          preserveHarmony: true,
          preferSubtlety: true,
          enforceBalance: true,
        },
        changedToken: colorToken
      });
      const newSuggestions = suggestionResult.suggestions.slice(0, 3); // Limit to 3 suggestions

      setSuggestions(newSuggestions);
      setIsAnalyzing(false);
    }, 500);
  }, [colorToken, currentColor, colors, previewColorChange]);

  // Apply a suggestion
  const applySuggestion = useCallback((suggestion: ColorSuggestion) => {
    const suggestedColor = suggestion.colors[colorToken] || suggestion.colors[Object.keys(suggestion.colors)[0]];
    if (suggestedColor) {
      setLocalColor(suggestedColor);
      previewColorChange(colorToken, suggestedColor);
      handleColorChange(suggestedColor);
      setSelectedSuggestion(suggestion.id);
    }
  }, [colorToken, previewColorChange, handleColorChange]);

  // Preview a suggestion (hover)
  const previewSuggestion = useCallback((suggestion: ColorSuggestion) => {
    const suggestedColor = suggestion.colors[colorToken] || suggestion.colors[Object.keys(suggestion.colors)[0]];
    if (suggestedColor) {
      previewColorChange(colorToken, suggestedColor);
    }
  }, [colorToken, previewColorChange]);

  // Revert preview on hover out
  const revertPreview = useCallback(() => {
    previewColorChange(colorToken, localColor);
  }, [colorToken, localColor, previewColorChange]);

  // Commit changes
  const handleCommit = useCallback(() => {
    updateColor(colorToken, localColor);
    setIsOpen(false);
    onColorChange?.(localColor);
  }, [colorToken, localColor, updateColor, onColorChange]);

  // Cancel changes
  const handleCancel = useCallback(() => {
    // Revert preview
    previewColorChange(colorToken, currentColor);
    setLocalColor(currentColor);
    setIsOpen(false);
    setSuggestions([]);
    setAnalysis(null);
  }, [colorToken, currentColor, previewColorChange]);

  // Handle click outside
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (editorRef.current && !editorRef.current.contains(e.target as Node)) {
        if (isOpen && localColor !== currentColor) {
          // Prompt to save changes (for now, just cancel)
          handleCancel();
        }
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isOpen, localColor, currentColor, handleCancel]);

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

  // Format HSL string for display
  const formatHSL = (color: HSLColor) => {
    return `HSL(${Math.round(color.h)}°, ${Math.round(color.s * 100)}%, ${Math.round(color.l * 100)}%)`;
  };

  // Convert HSL to CSS string
  const hslToCSS = (color: HSLColor) => {
    return `hsl(${color.h}, ${color.s * 100}%, ${color.l * 100}%)`;
  };

  return (
    <div style={{ position: 'relative' }} ref={editorRef}>
      {/* Collapsed View - Original Card Design */}
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
          transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)'
        }}
      >
        {/* Color Swatch */}
        <div
          style={{
            width: '100%',
            height: '64px',
            background: hslToCSS(localColor),
            borderRadius: 'var(--radius-sm)',
            marginBottom: 'var(--space-2)',
            border: '1px solid var(--border)'
          }}
          aria-label={`Color swatch: ${formatHSL(localColor)}`}
        />
        {/* Label */}
        <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
          {label}
        </div>
        {/* Token */}
        <code style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-family-mono)' }}>
          --{colorToken}
        </code>
        {/* Description */}
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 'var(--space-1)', margin: 0 }}>
          {description}
        </p>
      </motion.div>

      {/* Expanded Editor */}
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
                    width: '24px',
                    height: '24px',
                    borderRadius: 'var(--radius-sm)',
                    background: hslToCSS(localColor),
                    border: '1px solid var(--border)'
                  }}
                />
                <div>
                  <div style={{ fontWeight: 600, fontSize: '14px' }}>{label}</div>
                  <code style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-family-mono)' }}>
                    --{colorToken}
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
                aria-label="Close color editor"
                onMouseEnter={(e) => e.currentTarget.style.color = 'var(--text)'}
                onMouseLeave={(e) => e.currentTarget.style.color = 'var(--text-muted)'}
              >
                ×
              </button>
            </div>

            {/* Sliders */}
            <div style={{ padding: 'var(--space-6)' }}>
              <Slider
                min={0}
                max={360}
                value={localColor.h}
                onChange={(h) => handleColorChange({ ...localColor, h })}
                label="Hue"
                unit="°"
                gradient={`linear-gradient(to right,
                  hsl(0, ${localColor.s * 100}%, ${localColor.l * 100}%),
                  hsl(60, ${localColor.s * 100}%, ${localColor.l * 100}%),
                  hsl(120, ${localColor.s * 100}%, ${localColor.l * 100}%),
                  hsl(180, ${localColor.s * 100}%, ${localColor.l * 100}%),
                  hsl(240, ${localColor.s * 100}%, ${localColor.l * 100}%),
                  hsl(300, ${localColor.s * 100}%, ${localColor.l * 100}%),
                  hsl(360, ${localColor.s * 100}%, ${localColor.l * 100}%)
                )`}
              />

              <Slider
                min={0}
                max={100}
                value={localColor.s * 100}
                onChange={(s) => handleColorChange({ ...localColor, s: s / 100 })}
                label="Saturation"
                unit="%"
                gradient={`linear-gradient(to right,
                  hsl(${localColor.h}, 0%, ${localColor.l * 100}%),
                  hsl(${localColor.h}, 100%, ${localColor.l * 100}%)
                )`}
              />

              <Slider
                min={0}
                max={100}
                value={localColor.l * 100}
                onChange={(l) => handleColorChange({ ...localColor, l: l / 100 })}
                label="Lightness"
                unit="%"
                gradient={`linear-gradient(to right,
                  hsl(${localColor.h}, ${localColor.s * 100}%, 0%),
                  hsl(${localColor.h}, ${localColor.s * 100}%, 50%),
                  hsl(${localColor.h}, ${localColor.s * 100}%, 100%)
                )`}
              />
            </div>

            {/* Quality Indicators */}
            {analysis && (
              <div style={{
                padding: 'var(--space-4) var(--space-6)',
                borderTop: '1px solid var(--border)',
                borderBottom: '1px solid var(--border)',
                background: 'var(--bg-secondary)',
                display: 'flex',
                gap: 'var(--space-6)',
                fontSize: '13px'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Quality</span>
                  <span style={{ fontWeight: 600, fontFamily: 'var(--font-family-mono)' }}>
                    {analysis.quality.score.toFixed(1)}/10
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
                  <span style={{ color: 'var(--text-muted)' }}>Contrast</span>
                  <span style={{
                    fontWeight: 600,
                    color: analysis.contrast.wcagLevel === 'fail' ? 'var(--color-error)' : 'var(--color-success)'
                  }}>
                    {analysis.contrast.wcagLevel === 'AAA' && 'AAA'}
                    {analysis.contrast.wcagLevel === 'AA' && 'AA'}
                    {analysis.contrast.wcagLevel === 'fail' && 'Fails'}
                  </span>
                </div>
                {analysis.semantics && !analysis.semantics.fitsRole && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    color: 'var(--color-attention)',
                    fontSize: '12px'
                  }}>
                    <span>Role mismatch</span>
                  </div>
                )}
              </div>
            )}

            {/* AI Suggestions */}
            {suggestions.length > 0 && (
              <div style={{ padding: 'var(--space-6)' }}>
                <div style={{
                  fontSize: '13px',
                  fontWeight: 600,
                  marginBottom: 'var(--space-3)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between'
                }}>
                  <span>AI Suggestions</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-muted)', fontWeight: 400 }}>
                    {isAnalyzing ? 'Analyzing...' : `${suggestions.length} options`}
                  </span>
                </div>
                <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
                  {suggestions.map((suggestion) => (
                    <motion.div
                      key={suggestion.id}
                      whileHover={{ scale: 1.005 }}
                      onHoverStart={() => previewSuggestion(suggestion)}
                      onHoverEnd={revertPreview}
                      style={{
                        padding: 'var(--space-3)',
                        borderRadius: 'var(--radius-md)',
                        background: selectedSuggestion === suggestion.id ? 'var(--color-hover)' : 'var(--bg-secondary)',
                        border: `1px solid ${selectedSuggestion === suggestion.id ? 'var(--text-muted)' : 'var(--border)'}`,
                        cursor: 'pointer',
                        transition: 'all 150ms cubic-bezier(0.4, 0, 0.2, 1)'
                      }}
                    >
                      <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
                        <div style={{ display: 'flex', gap: '6px' }}>
                          {Object.values(suggestion.colors).slice(0, 3).map((color, idx) => (
                            <div
                              key={idx}
                              style={{
                                width: '32px',
                                height: '32px',
                                borderRadius: 'var(--radius-sm)',
                                background: hslToCSS(color),
                                border: '1px solid var(--border)'
                              }}
                            />
                          ))}
                        </div>
                        <div style={{ flex: 1 }}>
                          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
                            {suggestion.name}
                          </div>
                          <div style={{ fontSize: '12px', color: 'var(--text-muted)', marginBottom: 'var(--space-1)' }}>
                            {suggestion.description}
                          </div>
                          <div style={{ fontSize: '11px', color: 'var(--text-muted)', fontFamily: 'var(--font-family-mono)' }}>
                            Quality {suggestion.quality.overall.toFixed(1)}/10
                          </div>
                        </div>
                        <button
                          onClick={(e) => {
                            e.stopPropagation();
                            applySuggestion(suggestion);
                          }}
                          style={{
                            padding: 'var(--space-2) var(--space-4)',
                            fontSize: '12px',
                            fontWeight: 500,
                            borderRadius: 'var(--radius-sm)',
                            background: 'var(--primary)',
                            color: 'white',
                            border: 'none',
                            cursor: 'pointer',
                            transition: 'transform 100ms, opacity 150ms',
                            whiteSpace: 'nowrap'
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
                          Apply
                        </button>
                      </div>
                    </motion.div>
                  ))}
                </div>
              </div>
            )}

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