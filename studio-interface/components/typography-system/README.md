# Interactive Typography System

**Purpose:** Enable users to choose and preview fonts with the same refined aesthetic as the ColorEditor. Changes update instantly across the entire interface.

## Features

### Live Font Selection
- Click any font card to open the interactive editor
- Preview fonts in real-time as you hover over options
- See changes instantly across the entire interface
- Curated font library with categories (sans-serif, serif, mono, display)

### Font Categories

**Heading Fonts** - Headlines and section titles
- Sans-serif, serif, and display fonts
- Default: Sora

**Body Fonts** - Primary text content
- Sans-serif and serif fonts optimized for readability
- Default: Geist Sans

**Monospace Fonts** - Code and technical text
- Monospace fonts with excellent legibility
- Default: Geist Mono

### Design Principles

**Aesthetic:** Precise, confident, luxury font selection experience
- Same Swedish design studio aesthetic as ColorEditor
- Subtle hover states (1.01 scale)
- Smooth transitions (150ms cubic-bezier)
- 200px minimum width cards
- 64px preview area

**UX Flow:**
1. Collapsed card shows current font with preview sample
2. Click to expand modal with font list
3. Search and filter fonts by name or category
4. Hover to preview font in real-time
5. Click to select, then "Apply Changes" to commit

## Usage

### In ComponentShowcase

The typography section automatically uses the InteractiveTypographySystem:

```tsx
import { useTypographyStore } from '../state/typographyStore';

function InteractiveTypographySystem() {
  const { fonts, isInitialized, initializeFromCSS } = useTypographyStore();
  // ... renders FontEditor for each font token
}
```

### Standalone FontEditor

```tsx
import { FontEditor } from '@/components/typography-system/FontEditor';

<FontEditor
  fontToken="heading"
  currentFont="'Sora', sans-serif"
  label="Heading Font"
  description="Headlines and section titles"
  sampleText="Design Intelligence"
  onFontChange={(font) => console.log('Font changed:', font)}
/>
```

### Props

**FontEditor**
- `fontToken`: 'heading' | 'body' | 'mono'
- `currentFont`: string - Current font family value
- `label`: string - Display label
- `description`: string - Purpose description
- `sampleText`: string (optional) - Custom preview text
- `onFontChange`: (font: string) => void (optional)

## Store API

**useTypographyStore**

```typescript
const {
  fonts,              // Current font palette
  updateFont,         // Commit font change
  previewFontChange,  // Preview without committing
  clearPreview,       // Clear preview
  undo,              // Undo last change
  redo,              // Redo last undone change
  initializeFromCSS  // Initialize from CSS variables
} = useTypographyStore();
```

## CSS Variables

The system manages these CSS variables:

- `--font-family-heading`: Heading font with fallbacks
- `--font-family-body`: Body font with fallbacks
- `--font-family-mono`: Monospace font with fallbacks

Changes are:
- Applied instantly via `requestAnimationFrame`
- Persisted to localStorage
- Maintained in undo/redo history

## Font Library

### Sans-serif
- Sora (Studio default heading)
- Geist Sans (Studio default body)
- Inter (Humanist, highly legible)
- SF Pro (Apple system)
- Helvetica Neue (Classic)

### Serif
- Crimson Pro (Editorial, elegant)
- Merriweather (Readable)
- Georgia (Classic, web-safe)

### Monospace
- Geist Mono (Studio default)
- Fira Code (With ligatures)
- SF Mono (Apple mono)
- Consolas (Windows code)

### Display
- Poppins (Geometric, modern)
- Outfit (Rounded, friendly)

## Architecture

**Modular Bricks:**
- `FontEditor.tsx` - Interactive font editor component
- `typographyStore.ts` - Zustand state management
- Font injection handled via CSS variable injection (same system as colors)

**Data Flow:**
1. User clicks font → `previewFontChange()` → CSS injected
2. User hovers option → Preview updates instantly
3. User clicks "Apply" → `updateFont()` → History entry created
4. Changes persist to localStorage

## Keyboard Shortcuts

- `Enter` - Apply changes
- `Escape` - Cancel and revert
- Type to search fonts

## Quality Standards

- ✅ 9.5/10 quality baseline - Refined, not generic
- ✅ Matches ColorEditor aesthetic exactly
- ✅ 60fps performance via requestAnimationFrame
- ✅ Keyboard accessible
- ✅ Undo/redo support
- ✅ LocalStorage persistence
- ✅ Swedish design aesthetic (subtle, purposeful)

## Philosophy Alignment

**Five Pillars:**
1. **Purpose Drives Execution** - Clear why: Enable confident font selection
2. **Craft Embeds Care** - 9.5/10 polish in every detail
3. **Constraints Enable Creativity** - Curated font library, not overwhelming
4. **Intentional Incompleteness** - Users can extend font library
5. **Design for Humans** - Preview shows exactly what you get

**Nine Dimensions:**
- **Style** - Swedish aesthetic, German car facility precision
- **Motion** - 150ms transitions, subtle hover states
- **Voice** - "Live Typography System" - clear, confident
- **Space** - 200px grid, consistent with ColorEditor
- **Color** - Uses design system tokens
- **Typography** - Shows fonts in their own style
- **Proportion** - 64px preview area matches color swatch
- **Texture** - Subtle depth through shadows and borders
- **Body** - Click targets meet minimum 44px standards

---

**Remember:** The artifact is the container. The experience is the product. This isn't just a font picker—it's a moment of confident choice where users see their words transform before their eyes.
