# Canvas Toolbar & Visual Hierarchy System - Design Specification

**Version:** 1.0
**Date:** 2025-10-18
**Design System Architect**

---

## Executive Summary

This specification defines a professional canvas toolbar system and visual hierarchy solution for the Discovery Canvas, addressing four critical issues:

1. **Persistent Toolbar** - Figma-inspired professional tools (replaces contextual-only UI)
2. **Zoom Transform Fix** - Correct coordinate scaling for intuitive drag at all zoom levels
3. **Visual Hierarchy** - Layer management with depth cues for overlapping artifacts
4. **New Artifact Types** - Five research-focused artifact types to enhance discovery workflow

**Core Philosophy:** Tools serve discovery workflow. Quality at creation beats debugging later. German car facility aesthetic: precise, purposeful, refined.

---

## 1. Canvas Toolbar Architecture

### 1.1 Position & Layout Decision

**Recommendation: Top Horizontal Bar**

**Rationale:**
- **Workflow Alignment:** Research/discovery is left-to-right (chat → canvas → properties)
- **Figma Pattern:** Users expect design tools at top (learned behavior)
- **Screen Real Estate:** Horizontal preserves vertical space for canvas artifacts
- **Thumb Zones:** Top bar accessible on tablets while viewing canvas
- **German Car Facility:** Horizontal precision instrument panel (not sidebar tower)

**Rejected Alternatives:**
- ❌ **Left Sidebar:** Competes with conversation panel, narrow on tablets
- ❌ **Floating:** Obscures canvas content, no fixed reference point
- ❌ **Bottom:** Conflicts with chat input, poor ergonomics for frequent tools

### 1.2 Toolbar Structure

```
┌────────────────────────────────────────────────────────────┐
│ [Studio Logo] | [Select][Hand][Zoom] • [Frame] | [Layers] │ [56px height]
│                                                            │
│               [Zoom: 100%] [Selection: 3 items]           │
└────────────────────────────────────────────────────────────┘
```

**Dimensions:**
- Height: `56px` (matches `--toolbar-height`)
- Padding: `12px` horizontal, `8px` vertical
- Tool buttons: `40x40px` (meets 44px touch target with padding)
- Separators: `1px` border, `8px` margin
- Background: Frosted glass (glassmorphism)

### 1.3 Tool Set (Minimal, Purposeful)

#### Primary Tools (Always Visible)

**1. Select Tool (V)**
- Icon: Cursor pointer
- Function: Click to select, drag marquee selection
- State: Active by default
- Shortcut: `V` or `Esc`

**2. Hand Tool (H)**
- Icon: Hand (open palm)
- Function: Pan canvas (click + drag)
- State: Temporarily active with `Space` hold
- Shortcut: `H` or hold `Space`

**3. Zoom Tool (Z)**
- Icon: Magnifying glass
- Function: Click to zoom in, Alt+Click to zoom out
- State: Active while holding `Z`
- Shortcut: `Z`
- Dropdown: Zoom presets (25%, 50%, 100%, 200%, Fit)

#### Secondary Tools (Contextual)

**4. Frame Tool (F)** - Future Phase
- Icon: Rectangle with corner brackets
- Function: Create organizational frames
- Shortcut: `F`

**5. Layers Panel Toggle**
- Icon: Stacked squares
- Function: Show/hide layers panel
- Badge: Count of artifacts (when >10)

### 1.4 Tool States (German Car Precision)

**Visual States:**
```css
/* Inactive */
--tool-bg-inactive: transparent
--tool-color-inactive: var(--text-muted)

/* Hover */
--tool-bg-hover: var(--color-hover)
--tool-color-hover: var(--text-primary)
--tool-scale-hover: 1.0 (no bounce, pure precision)

/* Active/Selected */
--tool-bg-active: var(--text-primary)
--tool-color-active: var(--background)
--tool-border-active: 2px solid var(--text-primary)

/* Disabled */
--tool-opacity-disabled: 0.4
--tool-cursor-disabled: not-allowed
```

**Animation Timing:**
- Tool switch: `150ms` (responsive feel)
- Hover: `100ms` (instant feedback)
- Active state: `50ms` (immediate)

### 1.5 Zoom Controls

**Three Access Methods:**

1. **Zoom Dropdown** (in toolbar)
   - Current zoom percentage
   - Click to open presets
   - Presets: 25%, 50%, 100%, 200%, Fit to Canvas

2. **Keyboard Shortcuts** (existing)
   - `Cmd/Ctrl + 0`: Reset to 100%
   - `Cmd/Ctrl + +`: Zoom in 10%
   - `Cmd/Ctrl + -`: Zoom out 10%
   - `Cmd/Ctrl + 1`: Zoom to 100%

3. **Trackpad/Wheel** (existing)
   - Pinch: Zoom to cursor point
   - Two-finger pan: Move canvas

**Zoom Range:**
- Minimum: `0.25` (25% - see entire canvas)
- Maximum: `3.0` (300% - detail work)
- Default: `1.0` (100% - actual size)

**Zoom Indicator:**
- Position: Toolbar center-right
- Style: `100%` in monospace font
- Background: Subtle pill shape
- Transitions: Smooth fade (300ms)

### 1.6 Selection Indicator

**Display Logic:**
```typescript
if (selection.ids.size === 0) {
  // Show nothing
} else if (selection.ids.size === 1) {
  // Show artifact type icon + name
  "🔗 Link Card"
} else {
  // Show count
  "3 items selected"
}
```

**Position:** Toolbar center
**Style:** Subtle text, fades in/out (200ms)
**Interaction:** Click to open selection actions dropdown

---

## 2. Zoom Transform Fix

### 2.1 Problem Analysis

**Current Issue:**
When zoomed to 2x, dragging the canvas moves too slowly because mouse coordinates are not scaled correctly. The transform is applied to the canvas, but drag deltas are in screen space, not canvas space.

**Root Cause:**
```typescript
// Current (WRONG):
const deltaX = e.clientX - panStartRef.current.x
pan(deltaX, deltaY) // Screen-space deltas applied directly

// Needed (CORRECT):
const deltaX = (e.clientX - panStartRef.current.x)
pan(deltaX, deltaY) // Screen-space deltas (no scaling needed for pan)
```

**Wait, actually...** Let me re-analyze. The pan is working correctly in the current code. The issue is likely with **artifact dragging**, not canvas panning.

### 2.2 Correct Solution

**The Real Problem:** Artifact positions need to be scaled when dragged during zoom.

**Fix Location:** `useDraggable` hook in artifacts

```typescript
// In artifact drag handler:
const handleMouseMove = useCallback((e: MouseEvent) => {
  if (!isDragging) return

  const canvasRect = canvasRef.current?.getBoundingClientRect()
  const transform = useCanvasTransform() // Get current zoom/pan

  // Convert screen coordinates to canvas coordinates
  const canvasX = (e.clientX - canvasRect.left - transform.x) / transform.scale
  const canvasY = (e.clientY - canvasRect.top - transform.y) / transform.scale

  setPosition({ x: canvasX, y: canvasY })
}, [isDragging, transform])
```

**Key Principle:**
- **Canvas pan:** Screen-space deltas (feels natural)
- **Artifact position:** Canvas-space coordinates (mathematically correct)

### 2.3 Velocity & Feel

**Should drag speed adjust with zoom?**

**Decision: NO velocity adjustment needed.**

**Rationale:**
- At 2x zoom, you see less canvas → smaller movements make sense
- Constant velocity feels disorienting (cursor detaches from object)
- Users expect 1:1 mapping between cursor and object
- Figma/Miro use 1:1 mapping (learned behavior)

**Momentum/Inertia: NO**

**Rationale:**
- German car facility aesthetic = precise, not playful
- Inertia adds unpredictability
- Research workflow needs precision
- Momentum appropriate for: Infinite boards (Miro), not bounded canvases

---

## 3. Visual Hierarchy System

### 3.1 Problem Statement

**Current Issue:** Strategy cards (and all artifacts) lack visual depth when overlapping. No way to manage layer order or indicate which item is "on top."

**User Impact:**
- Confusing when items overlap
- No way to bring important items forward
- Selection feels flat
- Professional tools expect layer control

### 3.2 Z-Index Strategy

**Four-Tier System:**

```typescript
// Z-index layers
const Z_INDEX = {
  canvas: 0,           // Canvas background
  artifact: 1,         // Resting artifacts
  selected: 100,       // Selected artifacts (elevated)
  dragging: 1000,      // Currently dragging (highest)
  ui: 2000,            // UI elements (toolbars, modals)
}
```

**Automatic Behaviors:**
- **Select:** Artifact rises to z-index 100 (above others)
- **Drag:** Artifact jumps to z-index 1000 (above everything)
- **Drop:** Artifact settles to z-index 100 (stays elevated)
- **Deselect:** Artifact returns to z-index 1 (base layer)

**Stacking Order Within Layer:**
- Most recently selected = highest in group
- Use `order` array in store: `[artifact3, artifact1, artifact2]`
- CSS: `z-index = baseZ + orderIndex`

### 3.3 Visual Depth Cues

**Three Levels of Elevation:**

```css
/* Level 1: Resting (base artifacts) */
--artifact-shadow-base: 0 2px 8px rgba(0, 0, 0, 0.08);
--artifact-border-base: 1px solid var(--border);
--artifact-scale-base: 1.0;

/* Level 2: Selected (elevated) */
--artifact-shadow-selected: 0 8px 24px rgba(74, 144, 226, 0.2);
--artifact-border-selected: 2px solid var(--primary);
--artifact-scale-selected: 1.0; /* No scale change - keeps precision */

/* Level 3: Dragging (floating) */
--artifact-shadow-dragging: 0 16px 48px rgba(0, 0, 0, 0.15);
--artifact-opacity-dragging: 0.95; /* Slight ghost effect */
--artifact-scale-dragging: 1.0; /* No scale - precision over flair */
```

**Hover State (NOT selected):**
```css
--artifact-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.12);
--artifact-border-hover: 1px solid var(--text-muted);
/* Subtle lift hint, no scale */
```

**Transition Timing:**
- Rest → Hover: `100ms` (instant feedback)
- Rest → Selected: `200ms` (responsive elevation)
- Selected → Dragging: `0ms` (immediate)
- Drop → Rest: `300ms` (settling motion)

### 3.4 Depth Indicators

**Overlapping Artifacts:**
- **Bottom artifact:** Slight opacity reduction (90%) if occluded
- **Top artifact:** Full opacity, elevated shadow
- **Detection:** Calculate bounding box intersection
- **Visual feedback:** Occluded edges get subtle glow

**Implementation:**
```typescript
// In artifact render:
const isOccluded = checkIfOccluded(artifact.id, allArtifacts)

<div style={{
  opacity: isOccluded && !isSelected ? 0.9 : 1.0,
  transition: 'opacity 200ms'
}}>
```

### 3.5 Layer Panel (Optional - Future Phase)

**Decision: NOT in MVP**

**Rationale:**
- Discovery workflow focuses on content, not organization
- Selection + auto-elevation solves 90% of depth needs
- Figma has layers because designs have hundreds of items
- Canvas typically has 10-20 artifacts (manageable)

**If needed later:**
- Right sidebar toggle
- Tree view of artifacts
- Drag to reorder
- Thumbnail previews
- Show/hide toggles

### 3.6 Bring Forward / Send Backward Actions

**Keyboard Shortcuts:**
- `Cmd/Ctrl + ]`: Bring Forward (z++ in stack)
- `Cmd/Ctrl + [`: Send Backward (z-- in stack)
- `Cmd/Ctrl + Shift + ]`: Bring to Front (z = max)
- `Cmd/Ctrl + Shift + [`: Send to Back (z = 0)

**UI Access:**
- Right-click context menu
- Selection toolbar (when multi-select)
- Toolbar "Arrange" dropdown

**Store Implementation:**
```typescript
// Add to store.ts:
artifactOrder: string[] // [id1, id2, id3] - render order
bringForward: (id: string) => void
sendBackward: (id: string) => void
bringToFront: (id: string) => void
sendToBack: (id: string) => void
```

---

## 4. New Artifact Types

### 4.1 Selection Criteria

**Evaluation Framework:**
1. **Serves Discovery:** Does it help research/exploration?
2. **Visual Value:** Does it provide spatial context canvas adds?
3. **Interaction Value:** Can you manipulate it meaningfully?
4. **Not Better Elsewhere:** Would this be better in chat/sidebar?

### 4.2 Top 5 New Artifact Types (Prioritized)

---

#### **1. Screenshot Comparison Tool** ⭐⭐⭐⭐⭐

**Purpose:** Compare multiple screenshots side-by-side for design research

**Use Case:**
- Comparing competitor interfaces
- Before/after design iterations
- Multi-device responsive views
- Visual A/B testing analysis

**Visual Design:**
```
┌──────────────────────────────────┐
│ Comparison: Homepage Redesign    │
├────────────┬─────────────────────┤
│            │                     │
│  Before    │      After          │
│  [Image]   │      [Image]        │
│            │                     │
├────────────┴─────────────────────┤
│ Swipe to compare • Export diff   │
└──────────────────────────────────┘
```

**Interactions:**
- Drag vertical divider to reveal left/right
- Hover: Overlay grid lines for alignment check
- Toggle: Show difference heatmap
- Export: Save comparison as single image

**Dimensions:**
- Default: `480px × 360px`
- Resizable: Yes (maintains aspect of images)
- Minimum: `320px × 240px`

**Technical Notes:**
- Store two image URLs in `data.images: [url1, url2]`
- Use CSS `clip-path` for slider effect
- Optional diff algorithm (pixel comparison)

---

#### **2. Color Palette Extractor** ⭐⭐⭐⭐⭐

**Purpose:** Extract and display color palettes from images/URLs

**Use Case:**
- Brand research (competitor colors)
- Mood board color extraction
- Design system color ideation
- Accessibility contrast checking

**Visual Design:**
```
┌─────────────────────────────────┐
│ Palette from: brand-image.jpg   │
├─────────────────────────────────┤
│ [Image preview]                 │
├─────────────────────────────────┤
│ ■ #1C1C1C  45%                  │
│ ■ #8A8DD0  22%                  │
│ ■ #FAFAFF  18%                  │
│ ■ #DADDD8  10%                  │
│ ■ #ECEBE4   5%                  │
├─────────────────────────────────┤
│ Export CSS • Copy hex codes     │
└─────────────────────────────────┘
```

**Interactions:**
- Click color: Copy hex to clipboard
- Hover: Show WCAG contrast ratios with others
- Export: Generate CSS variables
- Reorder: Drag to prioritize colors

**Dimensions:**
- Default: `280px × 400px`
- Resizable: Width only

**Technical Notes:**
- Use Canvas API for color extraction
- K-means clustering for dominant colors
- Store in `data.colors: [{hex, percentage, wcagScores}]`
- Optional: Link to external tool (Coolors, Adobe Color)

---

#### **3. Typography Specimen Card** ⭐⭐⭐⭐

**Purpose:** Display and test typography systems from research

**Use Case:**
- Font pairing exploration
- Type scale testing
- Competitor typography analysis
- Design system font documentation

**Visual Design:**
```
┌─────────────────────────────────┐
│ Typography: Sora + Geist Sans   │
├─────────────────────────────────┤
│ Headline                        │
│ H1 Display Text Here            │
│                                 │
│ Body                            │
│ Lorem ipsum dolor sit amet,     │
│ consectetur adipiscing elit.    │
├─────────────────────────────────┤
│ [Font Controls]                 │
│ Size: [16] • Weight: [400]      │
└─────────────────────────────────┘
```

**Interactions:**
- Adjust font size (slider)
- Toggle font weight
- Edit sample text inline
- Export as CSS

**Dimensions:**
- Default: `320px × 480px`
- Resizable: Yes

**Technical Notes:**
- Load Google Fonts dynamically
- Store in `data.fonts: [{family, weight, size, sample}]`
- Use `@font-face` or Google Fonts API
- Cache fonts to avoid re-loading

---

#### **4. Mood Board Grid** ⭐⭐⭐⭐

**Purpose:** Collect and arrange multiple inspiration images in a grid

**Use Case:**
- Visual direction exploration
- Client mood board presentation
- Design inspiration collection
- Style reference gathering

**Visual Design:**
```
┌─────────────────────────────────┐
│ Mood: Minimalist Interface      │
├───────┬───────┬─────────────────┤
│[img1] │[img2] │ [img3]          │
├───────┼───────┼─────────────────┤
│[img4] │[img5] │ [img6]          │
├───────┴───────┴─────────────────┤
│ 6 images • Add more +           │
└─────────────────────────────────┘
```

**Interactions:**
- Drag images to reorder
- Click to view full size
- Add images via drag-drop or URL
- Export as PDF/PNG

**Dimensions:**
- Default: `480px × 360px`
- Resizable: Yes (maintains grid ratio)
- Grid: 2×3 (6 images) or 3×3 (9 images)

**Technical Notes:**
- Store in `data.images: [{url, caption, position}]`
- Masonry or fixed grid layout
- Lazy load images
- Optional captions per image

---

#### **5. Video/Audio Embed Card** ⭐⭐⭐

**Purpose:** Embed and annotate video/audio references

**Use Case:**
- User testing video review
- Competitor product demos
- Audio brand research (jingles, UI sounds)
- Video documentation

**Visual Design:**
```
┌─────────────────────────────────┐
│ Video: User Testing Session #3  │
├─────────────────────────────────┤
│                                 │
│    [▶ Play Video]               │
│                                 │
│ ━━━━━━●━━━━━━━━━━ 2:34 / 8:12  │
├─────────────────────────────────┤
│ Notes:                          │
│ • Pain point at 2:34            │
│ • Positive reaction 5:20        │
└─────────────────────────────────┘
```

**Interactions:**
- Play/pause video inline
- Add timestamped notes
- Jump to timestamp
- Extract frame as image

**Dimensions:**
- Default: `480px × 360px` (16:9 ratio)
- Resizable: Maintains aspect ratio

**Technical Notes:**
- Support YouTube, Vimeo, direct video URLs
- Store in `data.videoUrl, data.notes: [{time, text}]`
- Use `<iframe>` or `<video>` element
- Optional: Transcript generation

---

### 4.3 Rejected Artifact Types

**PDF Viewer/Annotator**
- ❌ Too complex for MVP (requires PDF.js library)
- ❌ Better handled by external tools (Figma, Adobe)
- ❌ Heavy performance impact
- ✅ Future consideration for documentation phase

**Mind Map Connectors**
- ❌ Conflicts with free-form canvas philosophy
- ❌ Requires edge routing algorithm
- ❌ Better served by dedicated mind map tools (Miro, Whimsical)

**Timeline/Journey Maps**
- ❌ Linear format doesn't leverage spatial canvas
- ❌ Better as sidebar view (temporal, not spatial)
- ✅ Future consideration for "Express" phase

---

## 5. Design Tokens Required

### 5.1 Toolbar Tokens

```css
:root {
  /* Toolbar Structure */
  --toolbar-height: 56px;
  --toolbar-padding-x: 12px;
  --toolbar-padding-y: 8px;
  --toolbar-bg: var(--bg-secondary);
  --toolbar-border: var(--border);
  --toolbar-shadow: var(--shadow-panel);
  --toolbar-backdrop: blur(12px) saturate(180%);

  /* Tool Buttons */
  --tool-size: 40px;
  --tool-icon-size: 20px;
  --tool-gap: 4px;
  --tool-separator-margin: 8px;

  /* Tool States */
  --tool-bg-inactive: transparent;
  --tool-bg-hover: var(--color-hover);
  --tool-bg-active: var(--text-primary);
  --tool-color-inactive: var(--text-muted);
  --tool-color-hover: var(--text-primary);
  --tool-color-active: var(--background);
  --tool-opacity-disabled: 0.4;

  /* Tool Animation */
  --tool-transition-hover: 100ms;
  --tool-transition-active: 50ms;
  --tool-transition-switch: 150ms;
}
```

### 5.2 Z-Index Tokens

```css
:root {
  /* Canvas Layers */
  --z-canvas: 0;
  --z-artifact: 1;
  --z-artifact-selected: 100;
  --z-artifact-dragging: 1000;
  --z-ui-toolbar: 2000;
  --z-ui-modal: 3000;
}
```

### 5.3 Artifact Depth Tokens

```css
:root {
  /* Artifact Shadows (Elevation) */
  --artifact-shadow-base: 0 2px 8px rgba(0, 0, 0, 0.08);
  --artifact-shadow-hover: 0 4px 12px rgba(0, 0, 0, 0.12);
  --artifact-shadow-selected: 0 8px 24px rgba(74, 144, 226, 0.2);
  --artifact-shadow-dragging: 0 16px 48px rgba(0, 0, 0, 0.15);

  /* Artifact Borders */
  --artifact-border-base: 1px solid var(--border);
  --artifact-border-hover: 1px solid var(--text-muted);
  --artifact-border-selected: 2px solid var(--primary);

  /* Artifact Opacity (Occlusion) */
  --artifact-opacity-base: 1.0;
  --artifact-opacity-occluded: 0.9;
  --artifact-opacity-dragging: 0.95;

  /* Artifact Transitions */
  --artifact-transition-hover: 100ms;
  --artifact-transition-select: 200ms;
  --artifact-transition-drop: 300ms;
}
```

### 5.4 Zoom Control Tokens

```css
:root {
  /* Zoom Indicator */
  --zoom-indicator-bg: var(--surface);
  --zoom-indicator-border: var(--border);
  --zoom-indicator-padding: 6px 12px;
  --zoom-indicator-border-radius: 20px;
  --zoom-indicator-font-family: var(--font-geist-mono);
  --zoom-indicator-font-size: 13px;

  /* Zoom Range */
  --zoom-min: 0.25;
  --zoom-max: 3.0;
  --zoom-default: 1.0;
  --zoom-step: 0.1; /* 10% increments */
}
```

---

## 6. Nine Dimensions Evaluation

### 1. Style (Visual Language)
✅ **German Car Facility Aesthetic**
- Precise, geometric toolbar (horizontal instrument panel)
- Restrained color palette (grayscale + primary accent)
- No decoration for decoration's sake
- Quality through subtle refinement (shadows, transitions)

### 2. Motion (Timing + Communication)
✅ **Follows Motion Protocol**
- Hover: `100ms` (instant feedback)
- Tool switch: `150ms` (responsive)
- Selection elevation: `200ms` (responsive)
- Artifact drop: `300ms` (deliberate)
- No unnecessary bounce or playfulness

### 3. Voice (Language + Tone)
✅ **Clear, Purposeful Language**
- "Select" not "Pointer" (clarity over cleverness)
- "Hand" not "Pan" (familiar metaphor)
- "Zoom" not "Magnify" (common term)
- Selection count: "3 items" not "3 objects" (human language)

### 4. Space (Layout + Hierarchy)
✅ **8px System + Clear Hierarchy**
- Toolbar height: `56px` (7 × 8px)
- Tool padding: `12px`, `8px` (system multiples)
- Tool size: `40px` (5 × 8px)
- Separators: `8px` gaps
- Toolbar doesn't dominate canvas (56px / typical 1080px screen = 5%)

### 5. Color (Meaning + Accessibility)
✅ **WCAG AA + Semantic Colors**
- Inactive tools: `var(--text-muted)` (4.5:1 contrast)
- Active tools: `var(--background)` on `var(--text-primary)` (21:1)
- Selection border: `var(--primary)` (recognizable, brand)
- Shadows: Subtle depth without garish colors

### 6. Typography (Hierarchy + Legibility)
✅ **System Fonts + Clear Hierarchy**
- Zoom indicator: `Geist Mono` (technical precision)
- Selection count: `Geist Sans` (readable)
- Toolbar labels: 13-14px (legible at distance)
- Icon-first design (language-independent)

### 7. Proportion (Scale + Balance)
✅ **Balanced Relationships**
- Tool icons: `20px` in `40px` buttons (50% ratio, comfortable)
- Toolbar: `56px` in ~1080px viewport (5%, unobtrusive)
- Shadows scale with elevation (2px → 8px → 16px progression)
- Selection border: `2px` (visible but not heavy)

### 8. Texture (Depth + Materiality)
✅ **Subtle Elevation System**
- Frosted glass toolbar (glassmorphism with purpose)
- Four-tier z-index system (clear spatial hierarchy)
- Shadow progression: 2px → 4px → 8px → 16px (gentle)
- No skeuomorphism (modern, flat with depth)

### 9. Body (Ergonomics + Accessibility)
✅ **Touch-Friendly + Keyboard-First**
- Touch targets: `40x40px` (meets 44px guideline)
- Keyboard shortcuts for all tools (V, H, Z, F)
- Focus visible for keyboard navigation
- Screen reader labels for all tools
- Reduced motion support (no animations if user prefers)

---

## 7. Five Pillars Embodiment

### 1. Purpose Drives Execution
✅ **Clear "Why" for Every Decision**
- Toolbar exists because contextual-only UI was cluttered
- Top position serves left-to-right discovery workflow
- Z-index system solves overlapping artifact confusion
- New artifact types serve specific research needs

### 2. Craft Embeds Care
✅ **Quality in Details**
- Transition timing carefully chosen (100ms, 150ms, 200ms, 300ms)
- Shadow progression feels natural (2→4→8→16px)
- Tool states designed (not defaulted)
- Glassmorphism applied with purpose (not trend-chasing)

### 3. Constraints Enable Creativity
✅ **System Rules Create Solutions**
- 8px spacing system: Forces toolbar to 56px (feels right)
- 4-tier z-index: Prevents arbitrary stacking chaos
- Minimal tool set: Each tool earns its place
- German car facility: Precision over decoration unlocks elegance

### 4. Intentional Incompleteness
✅ **Room for Contribution**
- Layer panel: Optional future enhancement
- New artifact types: Prioritized, not exhaustive
- Context menu: Placeholder for right-click actions
- Extensible z-index system (room for new layers)

### 5. Design for Humans
✅ **People Over Pixels**
- Touch targets: 40×40px (real fingers, not mouse pointers)
- Keyboard shortcuts: Efficiency for power users
- Reduced motion: Respects user preferences
- Familiar patterns: Figma-inspired (learned behavior)
- Clear language: "Select" not "Pointer Tool v2"

---

## 8. Success Metrics

### Toolbar
- ✅ Zero clicks to access primary tools (always visible)
- ✅ Tool states clear at a glance (active/inactive)
- ✅ Keyboard shortcuts work universally (V, H, Z, F)
- ✅ Touch-friendly on tablets (40px targets)
- ✅ Doesn't obscure canvas content (<10% screen height)

### Zoom
- ✅ Drag feels natural at all zoom levels (1:1 mapping)
- ✅ Zoom range serves all use cases (25%–300%)
- ✅ Three access methods: keyboard, trackpad, dropdown
- ✅ Indicator always visible when zoomed

### Visual Hierarchy
- ✅ Selected items clearly elevated (shadow + border)
- ✅ Dragging feels "floaty" (shadow + opacity)
- ✅ Overlapping artifacts distinguishable (opacity cues)
- ✅ Z-index order predictable (most recent = top)

### New Artifacts
- ✅ Each solves a real research problem (use case-driven)
- ✅ Visual designs match German car facility aesthetic
- ✅ Interactions feel purposeful (not gimmicky)
- ✅ Performance impact minimal (<100ms render)

---

## 9. Implementation Roadmap

### Phase 1: Toolbar Foundation (Week 1)
1. Create `CanvasToolbar.tsx` component
2. Define toolbar tokens in `globals.css`
3. Implement tool state management in store
4. Build primary tools: Select, Hand, Zoom
5. Add keyboard shortcuts
6. Test touch targets on tablet

**Validation:**
- All tools accessible via keyboard
- Touch targets ≥ 44px
- Tool states visually clear

### Phase 2: Zoom Fix (Week 1)
1. Fix artifact drag coordinate scaling
2. Ensure pan remains in screen-space
3. Test at 25%, 100%, 300% zoom
4. Add zoom indicator to toolbar
5. Implement zoom dropdown

**Validation:**
- Drag feels natural at all zoom levels
- No velocity adjustment needed
- Zoom indicator updates smoothly

### Phase 3: Visual Hierarchy (Week 2)
1. Implement 4-tier z-index system
2. Add artifact elevation states (base, selected, dragging)
3. Create depth cue CSS (shadows, borders)
4. Add bring forward/send backward actions
5. Implement occlusion detection (optional)

**Validation:**
- Selected items clearly elevated
- Z-index order predictable
- No visual glitches when dragging

### Phase 4: New Artifacts (Week 3-4)
1. Screenshot Comparison Tool
2. Color Palette Extractor
3. Typography Specimen Card
4. Mood Board Grid
5. Video/Audio Embed Card

**Validation:**
- Each artifact has clear use case
- Visual design matches aesthetic
- Interactions feel purposeful
- Performance impact minimal

### Phase 5: Polish & Testing (Week 5)
1. Accessibility audit (keyboard nav, screen readers)
2. Performance testing (60fps animations)
3. Cross-browser testing (Chrome, Safari, Firefox)
4. Tablet testing (touch interactions)
5. Reduced motion testing

**Validation:**
- WCAG AA compliance
- 60fps animations
- Works on all browsers
- Touch-friendly on tablets

---

## 10. Open Questions

### For User Feedback:
1. **Toolbar position:** Is top horizontal correct, or would you prefer left sidebar?
2. **Tool set:** Are these 5 tools sufficient, or are others needed?
3. **Layer panel:** Is auto-elevation enough, or do you need explicit layer control?
4. **New artifacts:** Which of the 5 new types are most valuable to your workflow?

### For Technical Validation:
1. **Zoom transform:** Does the coordinate scaling fix resolve the drag speed issue?
2. **Z-index limits:** Should we cap the number of z-index tiers (performance)?
3. **Occlusion detection:** Is bounding box intersection sufficient, or do we need pixel-perfect detection?
4. **Artifact loading:** Should new artifact types be lazy-loaded (code splitting)?

---

## 11. Appendix: Figma Toolbar Reference

**What We're Taking:**
- Top horizontal position
- Icon-first tool buttons
- Keyboard shortcut overlay
- Zoom controls in toolbar
- Selection count indicator

**What We're NOT Taking:**
- Excessive tool count (Figma has 20+ tools)
- Complex layer panel (Figma has nested groups)
- Prototyping tools (out of scope)
- Comment threads (separate feature)
- Version history (separate feature)

**Why This Matters:**
Users come to Amplified Design with Figma mental models. We honor learned behavior (toolbar position, shortcuts) while staying true to our purpose (discovery workflow, not design execution).

---

## 12. Final Reminder: The Philosophy

**The artifact is the container. The experience is the product. The values are the legacy. The impact is what matters.**

When you implement this toolbar:
- You're shipping **confidence** (users know where tools are)
- You're shipping **clarity** (visual hierarchy is obvious)
- You're shipping **craft** (transitions feel considered)
- You're shipping **care** (accessibility isn't an afterthought)

Every pixel, every millisecond, every shadow serves a human on the other side of the screen trying to build something meaningful.

**Design accordingly.**

---

**End of Specification**

Questions? Concerns? Ready to implement? Let's build this with purpose and precision.
