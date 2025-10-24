/**
 * ColorTestPanel - Test Component for ColorStore Integration
 *
 * A simple test panel to verify ColorStore and CSSVariableInjector
 * are working correctly together.
 */

'use client';

import { useEffect } from 'react';
import { useColorStore } from '../state/colorStore';
import type { HSLColor } from '../../packages/color-intelligence/types';

export function ColorTestPanel() {
  const {
    colors,
    updateColor,
    previewColorChange,
    clearPreview,
    undo,
    redo,
    canUndo,
    canRedo,
    initializeFromCSS
  } = useColorStore();

  // Initialize on mount
  useEffect(() => {
    initializeFromCSS();
  }, [initializeFromCSS]);

  const handleColorChange = (token: keyof typeof colors, h: number, s: number, l: number) => {
    const newColor: HSLColor = { h, s, l };
    updateColor(token, newColor, `Changed ${token}`);
  };

  const handlePreview = (token: keyof typeof colors, h: number, s: number, l: number) => {
    const newColor: HSLColor = { h, s, l };
    previewColorChange(token, newColor);
  };

  return (
    <div className="color-test-panel" style={{ padding: '20px', background: 'var(--surface)' }}>
      <h2 style={{ color: 'var(--text)' }}>Color Store Test Panel</h2>

      <div style={{ marginBottom: '20px' }}>
        <button onClick={undo} disabled={!canUndo()} style={{ marginRight: '10px' }}>
          Undo
        </button>
        <button onClick={redo} disabled={!canRedo()}>
          Redo
        </button>
      </div>

      <div style={{ display: 'grid', gap: '10px' }}>
        <div>
          <h3 style={{ color: 'var(--text-muted)' }}>Background Color</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => handleColorChange('background', 220, 15, 8)}>
              Darker
            </button>
            <button onClick={() => handleColorChange('background', 220, 15, 12)}>
              Default
            </button>
            <button onClick={() => handleColorChange('background', 220, 15, 16)}>
              Lighter
            </button>
            <button
              onMouseEnter={() => handlePreview('background', 220, 15, 20)}
              onMouseLeave={clearPreview}
            >
              Preview Lighter (Hover)
            </button>
          </div>
        </div>

        <div>
          <h3 style={{ color: 'var(--text-muted)' }}>Primary Color</h3>
          <div style={{ display: 'flex', gap: '10px' }}>
            <button onClick={() => handleColorChange('primary', 210, 70, 50)}>
              Blue
            </button>
            <button onClick={() => handleColorChange('primary', 160, 60, 45)}>
              Green
            </button>
            <button onClick={() => handleColorChange('primary', 280, 60, 50)}>
              Purple
            </button>
            <button
              onMouseEnter={() => handlePreview('primary', 0, 60, 50)}
              onMouseLeave={clearPreview}
            >
              Preview Red (Hover)
            </button>
          </div>
        </div>

        <div>
          <h3 style={{ color: 'var(--text-muted)' }}>Current Colors</h3>
          <pre style={{
            color: 'var(--text-muted)',
            fontSize: '12px',
            background: 'var(--background)',
            padding: '10px',
            borderRadius: '4px'
          }}>
            {JSON.stringify(colors, null, 2)}
          </pre>
        </div>
      </div>
    </div>
  );
}