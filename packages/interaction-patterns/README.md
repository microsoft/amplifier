# @amplified/interactions

Common interaction patterns for Amplified Design. High-quality, accessible, battle-tested primitives that make interfaces feel polished and professional.

## Philosophy

These aren't just "utility hooks" – they're **foundational interaction patterns** that should work perfectly out of the box. Every pattern follows Amplified Design principles:

- **Accessible by Default** - ARIA attributes, keyboard support, screen reader announcements
- **Composable** - Each hook does one thing well, combine them for complex behaviors
- **Adaptive** - Works with touch, mouse, keyboard, pen
- **Performant** - Optimized event handling, proper cleanup
- **Type-Safe** - Full TypeScript support with comprehensive types

## Installation

```bash
# In your workspace
npm install @amplified/interactions

# Or as a local package
"dependencies": {
  "@amplified/interactions": "file:../packages/interaction-patterns"
}
```

## Available Patterns

### Drag & Drop

#### `useDraggable`

Make any element draggable with mouse or touch.

```tsx
import { useDraggable } from '@amplified/interactions'

function DraggableCard() {
  const { ref, position, isDragging } = useDraggable({
    initialPosition: { x: 100, y: 100 },
    onDragEnd: (pos) => console.log('Dropped at', pos),
    bounds: 'window', // or 'parent' or custom bounds
  })

  return (
    <div
      ref={ref}
      style={{
        position: 'absolute',
        left: position.x,
        top: position.y,
        cursor: isDragging ? 'grabbing' : 'grab',
      }}
    >
      Drag me!
    </div>
  )
}
```

**Features:**
- Automatic boundary detection (window or parent element)
- Smart interactive element detection (won't drag from buttons, links, inputs)
- Optional drag handle for title-bar-style dragging
- Smooth performance with proper event cleanup
- Preserves text selection when not dragging

**API:**

```typescript
interface DraggableOptions {
  initialPosition?: { x: number; y: number }
  onDragEnd?: (position: { x: number; y: number }) => void
  bounds?: 'parent' | 'window' | {
    top: number
    left: number
    right: number
    bottom: number
  }
  handle?: string // CSS selector
}

interface DraggableResult {
  ref: React.RefObject<HTMLDivElement | null>
  position: { x: number; y: number }
  isDragging: boolean
  setPosition: (position: { x: number; y: number }) => void
  style: {
    position: 'absolute'
    left: number
    top: number
    cursor: 'grabbing' | 'grab'
    userSelect: 'none' | 'auto'
  }
}
```

**Advanced Usage:**

```tsx
// With drag handle
const { ref } = useDraggable({
  handle: '.drag-handle',
})

// With custom bounds
const { ref } = useDraggable({
  bounds: {
    top: 0,
    left: 0,
    right: 1000,
    bottom: 800,
  },
})

// With position persistence
const { ref, position } = useDraggable({
  initialPosition: savedPosition,
  onDragEnd: (pos) => {
    saveToDatabase(pos)
  },
})
```

## Coming Soon

- `useDropZone` - Create drop targets for drag & drop
- `useSortable` - Reorderable lists with smooth animations
- `useResizable` - Resize handles for panels and windows
- `useGesture` - Pan, pinch, rotate gestures
- `useFocusTrap` - Trap focus within modals and dialogs
- `useFocusRing` - Keyboard navigation indicators

## Usage in Studio Interface

All drag & drop functionality in the Studio Interface uses `@amplified/interactions`:

```tsx
// Before
import { useDraggable } from '@/lib/hooks/useDraggable'

// After
import { useDraggable } from '@amplified/interactions'
```

## Development

```bash
# Build the package
npm run build

# Watch mode for development
npm run dev
```

## Architecture

This package is part of the Amplified Design monorepo:

```
amplified-design/
├── packages/
│   └── interaction-patterns/          ← This package
│       ├── src/
│       │   ├── drag-drop/
│       │   │   ├── useDraggable.ts
│       │   │   └── index.ts
│       │   └── index.ts
│       └── package.json
│
└── studio-interface/                  ← Consumer
    ├── components/
    │   └── artifacts/
    │       ├── StickyNote.tsx        // uses useDraggable
    │       ├── LinkCard.tsx          // uses useDraggable
    │       └── ResearchPanel.tsx     // uses useDraggable
    └── package.json
```

## Why This Exists

Common interaction patterns like drag & drop should "just work" in any Amplified Design product. By centralizing these patterns:

1. **Consistency** - All products use the same, battle-tested implementations
2. **Quality** - One place to fix bugs and add features
3. **Accessibility** - Accessible by default, not an afterthought
4. **Productivity** - Developers can focus on features, not reinventing drag & drop

## License

MIT
