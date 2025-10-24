---
feature: CanvasToolbar
date: 2025-10-18
status: in-progress
project: studio-interface
tags: [canvas, toolbar, visual-hierarchy, zoom, discovery]
supersedes: null
related: []
---

# Canvas Toolbar & Visual Hierarchy System - Design Specification

**Status**: in-progress
**Project**: studio-interface
**Date**: 2025-10-18
**Agent**: Design System Architect

---

## Purpose & Context

**Why this exists**: Professional canvas toolbar system for Discovery Canvas with persistent tools and visual hierarchy management

**Problem solved**: Four critical issues:
1. Contextual-only UI lacks persistent professional tools
2. Zoom transform coordinate scaling breaks intuitive drag
3. Overlapping artifacts need depth cues and layer management
4. Limited artifact types constrain discovery workflow

**Emotional goal**: German car facility aesthetic - precise, purposeful, refined. Tools serve discovery workflow with Figma-level professionalism.

**Related decisions**: N/A (foundational spec)

---

## Design Decisions

### Aesthetic Brief
- **Style**: Figma-inspired professional tools with German car facility precision
- **Motion**: 100ms instant tool feedback, 200ms zoom transitions
- **Voice**: "Professional discovery tools" - precise, purposeful, refined
- **Space**: 56px top toolbar (meets 48px minimum), 8px system spacing
- **Color**: Toolbar background with subtle depth separation from canvas
- **Typography**: Tool labels in Geist Sans with clear hierarchy
- **Proportion**: 24x24px icons in 32px touch targets
- **Texture**: Subtle toolbar elevation, depth cues for artifact layers
- **Body**: 32px minimum touch targets for tool buttons

### Key Constraints
- Horizontal top bar (workflow alignment: left-to-right)
- Zoom transform must not break drag coordinates
- Visual hierarchy with layer management for overlapping artifacts
- Five new research-focused artifact types
- Maintains 60fps canvas performance
- Keyboard shortcuts for all tools
- Works on desktop and tablet

---

## Implementation Requirements

### Modules to Create/Modify

**New Components:**
- `studio-interface/components/canvas/CanvasToolbar.tsx` - Main toolbar container
- `studio-interface/components/canvas/ToolButton.tsx` - Individual tool button
- `studio-interface/components/canvas/ZoomControls.tsx` - Zoom indicator + controls
- `studio-interface/components/canvas/LayerPanel.tsx` - Layer management panel
- `studio-interface/components/canvas/tools/SelectTool.tsx` - Selection tool logic
- `studio-interface/components/canvas/tools/HandTool.tsx` - Pan tool logic
- `studio-interface/components/canvas/tools/ZoomTool.tsx` - Zoom tool logic
- `studio-interface/components/canvas/tools/FrameTool.tsx` - Frame creation tool

**Modified Components:**
- `studio-interface/components/CanvasDropZone.tsx` - Integrate toolbar, fix zoom transforms
- `studio-interface/state/store.ts` - Add tool state, layer state

**New State:**
```typescript
// Tool state
activeTool: 'select' | 'hand' | 'zoom' | 'frame'
selectedArtifacts: string[]
zoomLevel: number

// Layer state
layers: Array<{
  id: string
  artifactId: string
  zIndex: number
  visible: boolean
  locked: boolean
}>
```

### CSS Variables Required
Define in `studio-interface/app/globals.css`:
```css
/* Canvas Toolbar */
--toolbar-height: 56px;
--toolbar-bg: var(--color-surface);
--toolbar-border: var(--color-border);
--toolbar-shadow: 0 1px 3px rgba(0, 0, 0, 0.08);

/* Tool Buttons */
--tool-size: 32px;
--tool-icon-size: 24px;
--tool-bg: transparent;
--tool-bg-hover: var(--color-surface-hover);
--tool-bg-active: var(--color-primary);
--tool-color: var(--color-text-secondary);
--tool-color-active: var(--color-primary-contrast);
--tool-border-radius: var(--radius-sm);

/* Zoom Controls */
--zoom-bg: var(--color-surface);
--zoom-border: var(--color-border);
--zoom-text: var(--color-text-secondary);

/* Layer Panel */
--layer-panel-width: 280px;
--layer-item-height: 40px;
--layer-item-bg-hover: var(--color-surface-hover);
--layer-item-bg-selected: var(--color-primary-subtle);

/* Canvas Depth */
--canvas-artifact-shadow-default: 0 1px 2px rgba(0, 0, 0, 0.08);
--canvas-artifact-shadow-hover: 0 2px 8px rgba(0, 0, 0, 0.12);
--canvas-artifact-shadow-selected: 0 4px 16px rgba(0, 0, 0, 0.16);
```

### Success Criteria
- [ ] Functional: All tools work (select, hand, zoom, frame)
- [ ] Aesthetic: German car facility precision (Figma-level refinement)
- [ ] Accessibility: 32px touch targets, keyboard shortcuts, ARIA labels
- [ ] Performance: 60fps canvas performance maintained
- [ ] Keyboard: All tools accessible via shortcuts (V, H, Z, F)
- [ ] Touch: Works on tablet with touch + pen input
- [ ] Zoom: Coordinate transforms work correctly at all zoom levels
- [ ] Layers: Visual hierarchy with drag-to-reorder

---

## Rationale

**Why these choices**:
- **Purpose**: Professional discovery tools for research workflows (chat → canvas → properties)
- **Craft**: Figma-inspired precision, subtle depth cues, 24x24px icon grid
- **Constraints**: 56px toolbar (7 × 8px), 32px touch targets, 8px spacing system
- **Incompleteness**: Future: custom tool plugins, tool presets, workspace layouts
- **Humans**: Keyboard shortcuts, learned Figma patterns, thumb-zone tablet access

**Alternatives considered**:
- Left sidebar (rejected - competes with chat, narrow on tablets)
- Floating toolbar (rejected - obscures canvas, no fixed reference)
- Bottom toolbar (rejected - conflicts with chat input, poor ergonomics)
- Contextual-only (rejected - lacks persistent professional tools)

**References**:
- Figma (toolbar position, tool patterns)
- Miro (canvas zoom behavior)
- FigJam (frame tool interaction)
- Sketch (layer panel structure)

---

## Nine Dimensions Evaluation

- **Style**: Figma-inspired professional tools, German car facility aesthetic
- **Motion**: 100ms tool feedback (instant), 200ms zoom transitions (responsive)
- **Voice**: "Professional discovery tools" - precise, purposeful, refined
- **Space**: 56px toolbar height, 8px system spacing, left-to-right workflow
- **Color**: Subtle toolbar elevation, active tool highlight, depth shadows
- **Typography**: Geist Sans for tool labels, clear hierarchy
- **Proportion**: 24x24px icons in 32px targets, balanced toolbar composition
- **Texture**: Subtle toolbar shadow (0 1px 3px), artifact depth cues
- **Body**: 32px touch targets exceed 44px Apple guideline (toolbar context allows tighter spacing)

---

## Five Pillars Check

1. **Purpose Drives Execution**: Enable professional discovery workflow with persistent tools
2. **Craft Embeds Care**: 24x24px icon grid, precise keyboard shortcuts, Figma-level refinement
3. **Constraints Enable Creativity**: 56px = 7×8px, 32px targets, GPU-accelerated canvas
4. **Intentional Incompleteness**: Future custom tools, presets, collaborative cursors
5. **Design for Humans**: Learned Figma patterns, keyboard shortcuts, tablet thumb zones

---

## Implementation Details

### Toolbar Structure

```
┌────────────────────────────────────────────────────────────┐
│ [Studio Logo] | [Select][Hand][Zoom] • [Frame] | [Layers] │ [56px height]
│                                                            │
│               [Zoom: 100%] [Selection: 3 items]           │
└────────────────────────────────────────────────────────────┘
```

**Dimensions:**
- Toolbar height: 56px (7 × 8px)
- Tool buttons: 32px × 32px
- Icon size: 24px × 24px (2px stroke)
- Button spacing: 8px
- Section dividers: 1px border, 16px margin

**Tool Groups:**
1. **Navigation** (left): Select, Hand, Zoom
2. **Creation** (center): Frame, Text, Shape (future)
3. **Management** (right): Layers panel toggle

### Zoom Transform Fix

**Problem**: Drag coordinates break when canvas is zoomed

**Solution**: Apply inverse transform to pointer events:
```typescript
// Before: pointer position directly mapped to canvas
const canvasX = pointerX - canvasRect.left
const canvasY = pointerY - canvasRect.top

// After: apply inverse zoom transform
const canvasX = (pointerX - canvasRect.left) / zoomLevel
const canvasY = (pointerY - canvasRect.top) / zoomLevel
```

### Visual Hierarchy System

**Problem**: Overlapping artifacts need depth management

**Solution**: Layer panel + z-index management:
- Default z-index: timestamp order (newer on top)
- Drag to reorder in layer panel
- Visual depth cues: shadow intensity increases with z-index
- Selected artifact: elevated shadow (4-layer system)

### New Artifact Types

Five research-focused types:
1. **Frame** - Group related artifacts (wireframe container)
2. **Text Note** - Quick annotations (sticky note style)
3. **Image Reference** - Visual inspiration (drag-drop images)
4. **Link Card** - External references (auto-preview)
5. **Research Finding** - Structured insights (templated)

---

## Keyboard Shortcuts

- `V` - Select tool (default)
- `H` - Hand tool (pan canvas)
- `Z` - Zoom tool (click to zoom in, alt+click to zoom out)
- `F` - Frame tool (drag to create)
- `Space + Drag` - Temporary hand tool
- `Cmd/Ctrl + Mouse Wheel` - Zoom
- `Cmd/Ctrl + 0` - Reset zoom to 100%
- `Cmd/Ctrl + 1` - Zoom to fit
- `Cmd/Ctrl + ]` - Bring forward
- `Cmd/Ctrl + [` - Send backward

---

## Validation

```bash
# Run before committing
npm run validate:tokens  # CSS variables check
npx tsc --noEmit        # TypeScript check
npm run build           # Production build
```

All must pass.

---

## Testing Checklist

- [ ] Toolbar renders at 56px height
- [ ] All tool buttons are 32px × 32px with 24px icons
- [ ] Select tool: Click artifacts, multi-select with Shift
- [ ] Hand tool: Pan canvas by dragging
- [ ] Zoom tool: Click to zoom in, Alt+click to zoom out
- [ ] Frame tool: Drag to create frame, auto-snap to 8px grid
- [ ] Zoom indicator: Shows current zoom level, click to edit
- [ ] Layers panel: Shows all artifacts, drag to reorder
- [ ] Keyboard shortcuts work for all tools
- [ ] Zoom transform: Drag works correctly at 50%, 100%, 200% zoom
- [ ] Visual hierarchy: Shadow depth increases with z-index
- [ ] Touch: Works on tablet with 32px touch targets
- [ ] Accessibility: ARIA labels, keyboard navigation
- [ ] Performance: 60fps maintained with 50+ artifacts

---

## Future Enhancements (Phase 2)

- Custom tool plugins (user-defined tools)
- Tool presets (saved tool configurations)
- Workspace layouts (save/restore toolbar + panel positions)
- Collaborative cursors (show other users' active tools)
- Tool history (undo/redo stack)
- Measurement tools (rulers, guides, grids)
- Export tools (export selected artifacts)
- Version control (save canvas snapshots)
