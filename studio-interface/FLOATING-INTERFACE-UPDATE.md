# Floating Interface Update

## What Changed

Transformed the split-pane layout into a **full-canvas workspace** with a **floating, draggable chat panel** and **draggable artifacts**.

---

## Key Improvements

### 1. Full Canvas Space
- Chat no longer takes up 40% of screen
- Maximum room for visual artifacts
- Clean, spacious workspace

### 2. Floating Chat Panel
**Features:**
- 💬 Draggable anywhere on canvas
- 📍 Dockable to corners (↖ ↗ ↙ ↘)
- − Minimizable to save space
- ✋ Drag from header bar
- 🎯 Auto-positioned at top-left initially

**Size:**
- Default: 400px × 500px
- Minimized: 320px × 56px (header only)

### 3. Draggable Artifacts
**All artifacts are now draggable:**
- 🔗 Link Cards
- 📚 Research Panels
- 📝 Sticky Notes
- 🎯 Strategy Cards

**Drag behavior:**
- Grab and drag anywhere
- Shadow elevates when dragging
- Position persists when dropped
- Cursor changes: grab → grabbing

---

## New Files

### Core System
- [useDraggable.ts](lib/hooks/useDraggable.ts) - Reusable drag-and-drop hook
- [FloatingChatPanel.tsx](components/FloatingChatPanel.tsx) - Floating chat interface
- [DiscoveryWorkspaceV2.tsx](components/DiscoveryWorkspaceV2.tsx) - New full-canvas layout

### Updated Components
- [LinkCard.tsx](components/artifacts/LinkCard.tsx) - Now draggable
- [ResearchPanel.tsx](components/artifacts/ResearchPanel.tsx) - Now draggable
- [StickyNote.tsx](components/artifacts/StickyNote.tsx) - Now draggable
- [StrategyCard.tsx](components/artifacts/StrategyCard.tsx) - Now draggable

---

## Technical Implementation

### Drag Hook
```typescript
const { ref, position, isDragging } = useDraggable({
  initialPosition: { x: 100, y: 100 },
  onDragEnd: (newPosition) => {
    // Save position
  },
  bounds: 'window', // or 'parent' or custom bounds
  handle: '.drag-handle' // optional: only drag from specific element
})
```

### Chat Docking
```typescript
// Dock positions
const positions = {
  'bottom-right': { x: window.innerWidth - 440, y: window.innerHeight - 540 },
  'bottom-left': { x: 40, y: window.innerHeight - 540 },
  'top-right': { x: window.innerWidth - 440, y: 80 },
  'top-left': { x: 40, y: 80 },
}
```

### Artifact Position Persistence
When an artifact is dragged, the new position is saved to state:
```typescript
onDragEnd: (newPosition) => {
  onUpdate?.({ position: newPosition })
}
```

---

## User Experience

### Initial State
```
┌─────────────────────────────────────────────────┐
│  Studio - Discovery                             │
├─────────────────────────────────────────────────┤
│                                                 │
│  ┌────────────────┐                             │
│  │ 💬 Chat        │                             │
│  │ ↖ ↗ ↙ ↘   −   │                             │
│  │────────────────│                             │
│  │ Studio: What   │                             │
│  │ would you...   │                             │
│  │                │                             │
│  │ [Input]        │                             │
│  └────────────────┘                             │
│                                                 │
│             [Empty canvas]                      │
│                                                 │
└─────────────────────────────────────────────────┘
```

### With Artifacts
```
┌─────────────────────────────────────────────────┐
│  Studio - Discovery                             │
├─────────────────────────────────────────────────┤
│  ┌────────┐                    ┌──────────┐    │
│  │ Chat   │                    │ Research │    │
│  │ (dock) │     ┌──────────┐   │ Panel    │    │
│  └────────┘     │ Link     │   └──────────┘    │
│                 │ Card     │                    │
│                 └──────────┘   ┌──────────┐    │
│   ┌────────┐                   │ Strategy │    │
│   │ Sticky │                   │ Card     │    │
│   │ Note   │                   └──────────┘    │
│   └────────┘                                    │
│                                                 │
└─────────────────────────────────────────────────┘
```

All elements can be dragged and repositioned freely!

---

## Visual Feedback

### During Drag
- **Cursor**: Changes from `grab` to `grabbing`
- **Shadow**: Elevates (modal-level shadow)
- **Z-Index**: Moves to 1000 (front layer)
- **Transform**: Slight scale/rotation for sticky notes

### Docking
- Click corner arrows (↖ ↗ ↙ ↘) in chat header
- Chat smoothly moves to docked position
- Can still be dragged from any docked position

### Minimize
- Click `−` button in chat header
- Chat collapses to header only
- Click `□` to restore

---

## Benefits

### For Users
✅ Maximum canvas space
✅ Chat doesn't block view
✅ Organize artifacts visually
✅ Natural spatial organization
✅ Quick docking for common positions

### For Workflow
✅ Group related artifacts
✅ Position chat where needed
✅ Clear distinction between chat and canvas
✅ Feels like physical workspace

---

## Next Steps

### Short-term Enhancements
- [ ] Add snap-to-grid for artifacts
- [ ] Magnetic docking zones
- [ ] Keyboard shortcuts (arrows to move selection)
- [ ] Multi-select and group drag
- [ ] Undo/redo for positions

### Medium-term
- [ ] Save workspace layout
- [ ] Export canvas as image
- [ ] Zoom in/out on canvas
- [ ] Connection lines between related artifacts
- [ ] Layers/grouping system

### Long-term
- [ ] Collaboration (see others' cursors)
- [ ] Real-time sync of positions
- [ ] Templates for common layouts
- [ ] AI suggests optimal layout

---

## Testing Checklist

### Chat Panel
- [x] Drag chat by header
- [ ] Dock to all 4 corners
- [ ] Minimize and restore
- [ ] Chat stays functional while dragged
- [ ] Input works after repositioning

### Artifacts
- [x] Drag Link Card
- [x] Drag Research Panel
- [x] Drag Sticky Note
- [x] Drag Strategy Card
- [ ] Position persists during session
- [ ] No overlapping z-index issues

### Edge Cases
- [ ] Drag to edge of screen (shouldn't go off-screen)
- [ ] Multiple artifacts selected
- [ ] Rapid dragging
- [ ] Drag while chat is thinking
- [ ] Window resize with positioned elements

---

## Browser Compatibility

### Tested
- Chrome ✓
- (Add others as tested)

### Known Issues
- None yet

---

## Conclusion

The floating interface provides a much better distinction between chat and canvas, giving users maximum space to organize their ideas visually. The draggable chat panel can be positioned exactly where needed and doesn't dominate the screen.

**Status**: ✅ Implemented and ready for testing
