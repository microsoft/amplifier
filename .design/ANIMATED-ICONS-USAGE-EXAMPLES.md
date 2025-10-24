# Animated Icons - Usage Examples

**Quick reference for using animated icon variants in Studio**

Created: 2025-10-17
Location: `studio-interface/components/icons/animated/`

---

## Import Patterns

```typescript
// Import animated variants
import {
  AnimatedCheckIcon,
  AnimatedAlertIcon,
  AnimatedCopyIcon,
  AnimatedSendIcon,
  AnimatedPlusIcon,
  AnimatedCloseIcon,
  AnimatedSunIcon,
  AnimatedMoonIcon,
  AnimatedSparkleIcon,
  AnimatedUploadIcon,
  AnimatedMaximizeIcon,
} from '@/components/icons/animated'

// Import type if needed
import type { AnimatedIconProps } from '@/components/icons/animated'
```

---

## Props Interface

All animated icons extend the base `IconProps` with animation-specific props:

```typescript
interface AnimatedIconProps extends IconProps {
  isActive?: boolean          // Trigger animation state
  animationSpeed?: number     // Speed multiplier (0.5-2x)
  onAnimationComplete?: () => void  // Callback when animation finishes

  // Inherited from IconProps:
  size?: number | string      // Icon size (default: 24)
  color?: string              // Icon color (default: 'currentColor')
  strokeWidth?: number        // Stroke width (default: 2)
  className?: string          // Additional CSS classes
}
```

---

## Usage Examples by Category

### 1. Success Confirmation (CheckIcon)

**Use case:** Show success feedback after an action completes

```tsx
import { AnimatedCheckIcon } from '@/components/icons/animated'

// Example: Copy button with animated success
const CopyButton = () => {
  const [copied, setCopied] = useState(false)

  const handleCopy = async () => {
    await navigator.clipboard.writeText(content)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  return (
    <button onClick={handleCopy}>
      {copied ? (
        <AnimatedCheckIcon
          size={18}
          color="var(--color-success)"
          isActive={true}
        />
      ) : (
        'Copy'
      )}
    </button>
  )
}
```

**Animation:** Path draws in over 300ms with ease-out easing

---

### 2. Warning/Error Alert (AlertIcon)

**Use case:** Draw attention to errors or warnings

```tsx
import { AnimatedAlertIcon } from '@/components/icons/animated'

// Example: Form validation error
const FormError = ({ message }: { message: string }) => {
  return (
    <div className="error-message">
      <AnimatedAlertIcon
        size={20}
        color="var(--color-error)"
        isActive={true}
      />
      <span>{message}</span>
    </div>
  )
}
```

**Animation:** Subtle pulse (scale 1 → 1.05 → 1) repeating twice over 200ms

---

### 3. Copy Confirmation (CopyIcon)

**Use case:** Quick bounce feedback on copy action

```tsx
import { AnimatedCopyIcon } from '@/components/icons/animated'

// Example: Inline copy button
const QuickCopy = ({ text }: { text: string }) => {
  const [justCopied, setJustCopied] = useState(false)

  const handleClick = () => {
    navigator.clipboard.writeText(text)
    setJustCopied(true)
    setTimeout(() => setJustCopied(false), 1000)
  }

  return (
    <button onClick={handleClick} aria-label="Copy to clipboard">
      <AnimatedCopyIcon
        size={16}
        isActive={justCopied}
        onAnimationComplete={() => console.log('Copy animation done')}
      />
    </button>
  )
}
```

**Animation:** Quick scale bounce (1 → 1.1 → 1) over 100ms with spring easing

---

### 4. Send Action (SendIcon)

**Use case:** Confirm message sent

```tsx
import { AnimatedSendIcon } from '@/components/icons/animated'

// Example: Chat send button
const SendButton = ({ onSend, disabled }: SendButtonProps) => {
  const [sending, setSending] = useState(false)

  const handleSend = async () => {
    setSending(true)
    await onSend()
    setTimeout(() => setSending(false), 500)
  }

  return (
    <button onClick={handleSend} disabled={disabled || sending}>
      <AnimatedSendIcon
        size={20}
        isActive={sending}
        color={disabled ? 'var(--text-muted)' : 'var(--primary)'}
      />
    </button>
  )
}
```

**Animation:** Scale up + translate (1.1x scale, +2px right, -2px up) over 200ms

---

### 5. Hover Interactions (Plus/Close)

**Use case:** Interactive feedback on hover

```tsx
import { AnimatedPlusIcon, AnimatedCloseIcon } from '@/components/icons/animated'

// Example: Add button with hover animation
const AddButton = () => {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <button
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
    >
      <AnimatedPlusIcon
        size={24}
        isActive={isHovered}
      />
      Add Item
    </button>
  )
}

// Example: Close button with hover rotation
const CloseButton = ({ onClose }: { onClose: () => void }) => {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <button
      onClick={onClose}
      onMouseEnter={() => setIsHovered(true)}
      onMouseLeave={() => setIsHovered(false)}
      aria-label="Close"
    >
      <AnimatedCloseIcon
        size={20}
        isActive={isHovered}
      />
    </button>
  )
}
```

**Animation:**
- PlusIcon: Rotate 90° on hover (100ms)
- CloseIcon: Rotate 45° on hover (100ms)

---

### 6. Theme Toggle (Sun/Moon)

**Use case:** Visualize theme switching

```tsx
import { AnimatedSunIcon, AnimatedMoonIcon } from '@/components/icons/animated'

// Example: Theme toggle button
const ThemeToggle = () => {
  const [theme, setTheme] = useState<'light' | 'dark'>('light')

  const toggleTheme = () => {
    setTheme(prev => prev === 'light' ? 'dark' : 'light')
  }

  return (
    <button onClick={toggleTheme} aria-label="Toggle theme">
      {theme === 'light' ? (
        <AnimatedSunIcon
          size={24}
          isActive={true}
        />
      ) : (
        <AnimatedMoonIcon
          size={24}
          isActive={true}
        />
      )}
    </button>
  )
}
```

**Animation:**
- SunIcon: Rotate 180° + scale pulse (1 → 1.2 → 1) over 300ms
- MoonIcon: Scale in (0 → 1.2 → 1) + fade in over 300ms

---

### 7. AI Generation Indicator (SparkleIcon)

**Use case:** Show AI is actively generating content

```tsx
import { AnimatedSparkleIcon } from '@/components/icons/animated'

// Example: AI thinking indicator
const AIThinking = () => {
  return (
    <div className="ai-status">
      <AnimatedSparkleIcon
        size={20}
        color="var(--primary)"
        isActive={true}
      />
      <span>AI is thinking...</span>
    </div>
  )
}

// Example: Generation in progress badge
const GeneratingBadge = ({ isGenerating }: { isGenerating: boolean }) => {
  if (!isGenerating) return null

  return (
    <div className="generation-badge">
      <AnimatedSparkleIcon
        size={16}
        isActive={true}
        animationSpeed={1.5}  // Faster animation
      />
      Generating
    </div>
  )
}
```

**Animation:** Continuous rotation + scale pulse (1 → 1.1 → 1) looping every 500ms

---

### 8. Upload Action (UploadIcon)

**Use case:** Show file upload initiated

```tsx
import { AnimatedUploadIcon } from '@/components/icons/animated'

// Example: Upload button
const UploadButton = ({ onUpload }: { onUpload: (file: File) => void }) => {
  const [uploading, setUploading] = useState(false)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0]
    if (file) {
      setUploading(true)
      onUpload(file)
      setTimeout(() => setUploading(false), 1000)
    }
  }

  return (
    <>
      <input
        ref={fileInputRef}
        type="file"
        style={{ display: 'none' }}
        onChange={handleFileSelect}
      />
      <button onClick={() => fileInputRef.current?.click()}>
        <AnimatedUploadIcon
          size={20}
          isActive={uploading}
        />
        Upload File
      </button>
    </>
  )
}
```

**Animation:** Arrow bounces up (y: 0 → -4 → 0) over 300ms with spring easing

---

### 9. Panel Expansion (MaximizeIcon)

**Use case:** Visualize panel expanding

```tsx
import { AnimatedMaximizeIcon } from '@/components/icons/animated'

// Example: Maximize panel button
const MaximizeButton = ({
  isMaximized,
  onToggle
}: {
  isMaximized: boolean
  onToggle: () => void
}) => {
  return (
    <button onClick={onToggle} aria-label="Maximize panel">
      <AnimatedMaximizeIcon
        size={18}
        isActive={isMaximized}
      />
    </button>
  )
}
```

**Animation:** Scale from center (0.8 → 1) + opacity (0.6 → 1) over 200ms

---

## Advanced Usage Patterns

### Custom Animation Speed

Control animation speed with `animationSpeed` prop (0.5x - 2x multiplier):

```tsx
// Slower animation (2x duration)
<AnimatedCheckIcon isActive={true} animationSpeed={0.5} />

// Faster animation (0.5x duration)
<AnimatedCheckIcon isActive={true} animationSpeed={2} />

// Default speed (1x)
<AnimatedCheckIcon isActive={true} animationSpeed={1} />
```

### Animation Completion Callback

React to animation completion:

```tsx
const [showSuccess, setShowSuccess] = useState(false)

const handleComplete = () => {
  console.log('Animation finished')
  // Hide success message after animation
  setTimeout(() => setShowSuccess(false), 2000)
}

return (
  <AnimatedCheckIcon
    isActive={showSuccess}
    onAnimationComplete={handleComplete}
  />
)
```

### Conditional Animation

Only animate on specific conditions:

```tsx
const MessageStatus = ({ status }: { status: 'sending' | 'sent' | 'error' }) => {
  return (
    <>
      {status === 'sending' && <AnimatedSparkleIcon isActive={true} />}
      {status === 'sent' && <AnimatedCheckIcon isActive={true} />}
      {status === 'error' && <AnimatedAlertIcon isActive={true} />}
    </>
  )
}
```

### Combining with Tailwind/CSS Classes

```tsx
<AnimatedCheckIcon
  className="text-green-600 hover:text-green-700 transition-colors"
  size={24}
  isActive={true}
/>
```

---

## Accessibility Considerations

All animated icons automatically respect `prefers-reduced-motion`:

```tsx
// Users with reduced motion preference will see instant state change
// No code changes needed - handled internally by useReducedMotion()

<AnimatedCheckIcon isActive={true} />
// With prefers-reduced-motion: animation duration becomes 0ms
// Without prefers-reduced-motion: normal 300ms animation
```

### Screen Reader Support

Add appropriate ARIA labels:

```tsx
<button aria-label="Copy code to clipboard">
  <AnimatedCopyIcon isActive={copied} />
  {!copied && <span className="sr-only">Copy</span>}
  {copied && <span className="sr-only">Copied</span>}
</button>
```

### Focus States

Ensure focus is visible:

```tsx
<button className="focus:outline-2 focus:outline-offset-2 focus:outline-blue-500">
  <AnimatedPlusIcon isActive={isHovered} />
</button>
```

---

## Performance Tips

### 1. Avoid Unnecessary Re-renders

Memoize animation state:

```tsx
const animationState = useMemo(() => isActive, [isActive])

<AnimatedCheckIcon isActive={animationState} />
```

### 2. Lazy Load Animated Variants

For large apps, lazy load animated icons:

```tsx
const AnimatedCheckIcon = lazy(() =>
  import('@/components/icons/animated').then(m => ({
    default: m.AnimatedCheckIcon
  }))
)
```

### 3. Conditional Import

Only import animated variants where needed:

```tsx
// In components that need feedback
import { AnimatedCheckIcon } from '@/components/icons/animated'

// In static UI, use regular icons
import { CheckIcon } from '@/components/icons/Icon'
```

---

## Testing Animated Icons

### Visual Testing

```tsx
// In Storybook or component playground
export const AnimatedIconShowcase = () => {
  const [isActive, setIsActive] = useState(false)

  return (
    <div>
      <button onClick={() => setIsActive(!isActive)}>
        Toggle Animation
      </button>
      <AnimatedCheckIcon isActive={isActive} size={48} />
    </div>
  )
}
```

### Unit Testing

```tsx
import { render, screen } from '@testing-library/react'
import { AnimatedCheckIcon } from '@/components/icons/animated'

test('renders animated check icon', () => {
  render(<AnimatedCheckIcon isActive={true} />)
  const icon = screen.getByRole('img', { hidden: true })
  expect(icon).toBeInTheDocument()
})

test('calls onAnimationComplete callback', async () => {
  const handleComplete = jest.fn()
  render(
    <AnimatedCheckIcon
      isActive={true}
      onAnimationComplete={handleComplete}
    />
  )

  await waitFor(() => {
    expect(handleComplete).toHaveBeenCalled()
  }, { timeout: 500 })
})
```

---

## Common Patterns

### Success → Reset Flow

```tsx
const [success, setSuccess] = useState(false)

const handleAction = async () => {
  await performAction()
  setSuccess(true)
  // Reset after 2 seconds
  setTimeout(() => setSuccess(false), 2000)
}

return (
  <button onClick={handleAction}>
    {success ? (
      <AnimatedCheckIcon isActive={true} />
    ) : (
      'Save'
    )}
  </button>
)
```

### Loading → Success → Error Flow

```tsx
type Status = 'idle' | 'loading' | 'success' | 'error'

const [status, setStatus] = useState<Status>('idle')

return (
  <>
    {status === 'loading' && <AnimatedSparkleIcon isActive={true} />}
    {status === 'success' && <AnimatedCheckIcon isActive={true} />}
    {status === 'error' && <AnimatedAlertIcon isActive={true} />}
  </>
)
```

### Hover + Click Combination

```tsx
const [isHovered, setIsHovered] = useState(false)
const [wasClicked, setWasClicked] = useState(false)

return (
  <button
    onMouseEnter={() => setIsHovered(true)}
    onMouseLeave={() => setIsHovered(false)}
    onClick={() => {
      setWasClicked(true)
      setTimeout(() => setWasClicked(false), 300)
    }}
  >
    <AnimatedPlusIcon isActive={isHovered || wasClicked} />
  </button>
)
```

---

## Migration from Static Icons

To migrate from static to animated icons:

### Before:
```tsx
import { CheckIcon } from '@/components/icons/Icon'

<button>
  {copied && <CheckIcon size={16} />}
</button>
```

### After:
```tsx
import { AnimatedCheckIcon } from '@/components/icons/animated'

<button>
  {copied && <AnimatedCheckIcon size={16} isActive={true} />}
</button>
```

**Key changes:**
1. Import from `/animated/` instead of `/Icon`
2. Add `isActive` prop to trigger animation
3. Optionally add `onAnimationComplete` callback

---

## When NOT to Use Animated Icons

Keep icons static when:

- ❌ **Pure navigation** (sidebar links, breadcrumbs)
- ❌ **Static labels** (file type indicators, badges)
- ❌ **Decorative elements** (illustrations, diagrams)
- ❌ **High-frequency updates** (live data counters)
- ❌ **Dense UI** (data tables, long lists)

Use animated icons when:

- ✅ **State changes** (success, error, loading)
- ✅ **User actions** (copy, send, upload)
- ✅ **Interactive feedback** (hover, focus, click)
- ✅ **Process indicators** (generating, processing)
- ✅ **Attention mechanisms** (alerts, notifications)

---

## Reference

- **Guidelines:** [.design/ICON-ANIMATION-GUIDELINES.md](./ICON-ANIMATION-GUIDELINES.md)
- **Motion Protocol:** [CLAUDE.md](../CLAUDE.md) (lines 50-66)
- **Design Philosophy:** [FRAMEWORK.md](../FRAMEWORK.md)
- **Components:** `studio-interface/components/icons/animated/`

---

**Remember:** Animation is communication, not decoration. Every animation should serve a clear purpose in helping users understand system state and feedback.
