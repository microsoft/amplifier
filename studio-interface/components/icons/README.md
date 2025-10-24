# Studio Icon System

**Aesthetic:** German car facility - geometric, precise, functional

## Design Principles

### 1. Grid System
- **24×24px viewport** - All icons fit within this frame
- **2px stroke weight** - Default for clarity at all sizes
- **Pixel-perfect alignment** - Icons align to pixel grid

### 2. Geometric Construction
- **Round caps and joins** - Softer, more refined
- **Consistent angles** - 45° and 90° preferred
- **Optical balance** - Not mathematical centering, visual centering

### 3. Style Guidelines
- **Outlined style** - Stroke-based, not filled (except small details like dots)
- **Minimal details** - Only essential elements
- **2px internal spacing** - Minimum gap between elements

## Usage

```tsx
import { DesktopIcon, ConversationIcon } from '@/components/icons/Icon'

// Basic usage
<DesktopIcon />

// Custom size
<DesktopIcon size={32} />

// Custom color (uses currentColor by default)
<DesktopIcon color="var(--color-ai-message)" />

// Custom stroke width
<DesktopIcon strokeWidth={1.5} />

// With Tailwind classes
<DesktopIcon className="text-blue-500 hover:text-blue-600" />
```

## Icon Categories

### Device Icons
- `DesktopIcon` - Desktop/monitor view
- `TabletIcon` - Tablet view
- `MobileIcon` - Mobile phone view
- `WatchIcon` - Smartwatch view

### Panel Icons
- `ConversationIcon` - Chat/conversation panel
- `HistoryIcon` - Version history timeline
- `PropertiesIcon` - Properties/settings panel
- `InspirationIcon` - Inspiration board

### Action Icons
- `PlusIcon` - Add/create new
- `CloseIcon` - Close/dismiss
- `ChevronDownIcon` - Expand downward
- `ChevronUpIcon` - Collapse upward
- `ChevronLeftIcon` - Navigate left
- `ChevronRightIcon` - Navigate right
- `SendIcon` - Send message/submit

### State Icons
- `SparkleIcon` - AI thinking/generating
- `LoadingIcon` - Loading state (with spin animation)
- `CheckIcon` - Success/completed
- `AlertIcon` - Attention needed

### Content Icons
- `FileIcon` - Document/file
- `ImageIcon` - Image/photo
- `UploadIcon` - Upload file

## Creating New Icons

Follow these steps:

1. **Start with the base Icon component**
2. **Design on 24×24 grid with 2px stroke**
3. **Use SVG path/line/circle/rect primitives**
4. **Keep it simple** - if it needs more than 5-7 paths, simplify
5. **Test at multiple sizes** - 16px, 24px, 32px, 48px
6. **Ensure accessibility** - works in single color

### Template

```tsx
export const NewIcon: React.FC<IconProps> = (props) => (
  <Icon {...props}>
    {/* Your SVG paths here */}
    <path d="..." />
  </Icon>
)
```

## Motion

Icons can animate using our behavior system:

```tsx
// Instant hover feedback
<button className="transition-instant hover:scale-110">
  <PlusIcon />
</button>

// Loading spinner (built-in)
<LoadingIcon /> {/* Automatically spins */}

// Deliberate state change
<div className="transition-deliberate" style={{
  color: isActive ? 'var(--color-success)' : 'var(--text)'
}}>
  <CheckIcon />
</div>
```

## Accessibility

- Icons inherit `currentColor` by default (works with text color)
- Always include accessible labels for icon-only buttons
- Icons are decorative when accompanied by text

```tsx
// Icon-only button (needs aria-label)
<button aria-label="Close panel">
  <CloseIcon />
</button>

// Icon with text (icon is decorative)
<button>
  <ConversationIcon />
  <span>Conversation</span>
</button>
```

## Design Token Integration

Icons use our design tokens:

```tsx
// Using semantic colors
<SparkleIcon color="var(--color-ai-thinking)" />
<CheckIcon color="var(--color-success)" />
<AlertIcon color="var(--color-attention)" />

// Size matching touch targets
<button className="w-12 h-12"> {/* 48px touch target */}
  <PlusIcon size={24} />
</button>
```
