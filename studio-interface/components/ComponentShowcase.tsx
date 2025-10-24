'use client'

import { useState, useEffect, useCallback } from 'react'
import { ChatInput } from './chat/ChatInput'
import { TypingIndicator } from './chat/TypingIndicator'
import { EmptyState } from './EmptyState'
import { PhaseNavigator } from './PhaseNavigator'
import { ColorEditor } from './color-system/ColorEditor'
import { FontEditor } from './typography-system/FontEditor'
import { useColorStore } from '../state/colorStore'
import { useTypographyStore } from '../state/typographyStore'
import {
  ArrowRightIcon,
  CheckIcon,
  HomeIcon,
  PencilIcon,
  ProjectIcon,
  SunIcon,
  MoonIcon,
  DesktopIcon,
  TabletIcon,
  MobileIcon,
  WatchIcon,
  ConversationIcon,
  HistoryIcon,
  PropertiesIcon,
  InspirationIcon,
  PlusIcon,
  CloseIcon,
  ChevronDownIcon,
  ChevronUpIcon,
  ChevronLeftIcon,
  ChevronRightIcon,
  SendIcon,
  SparkleIcon,
  LoadingIcon,
  CopyIcon,
  AlertIcon,
  FileIcon,
  ImageIcon,
  UploadIcon,
  MinimizeIcon,
  MaximizeIcon,
  DockTopLeftIcon,
  DockTopRightIcon,
  DockBottomLeftIcon,
  DockBottomRightIcon,
  SettingsIcon,
  SearchIcon,
  GridIcon,
  LayersIcon,
  BoxIcon,
  MessageCircleIcon,
} from './icons/Icon'
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
} from './icons/animated'

/**
 * Component Showcase - Comprehensive design system browser
 *
 * Purpose: Display all components, foundations, and patterns in an interactive Storybook-like interface
 * Organized by category with live previews, code examples, props documentation, and accessibility info
 */

interface Component {
  id: string
  name: string
  category: string
  description: string
  variants: ComponentVariant[]
  props: PropDefinition[]
  code: string
  accessibility: string[]
}

interface ComponentVariant {
  name: string
  preview: React.ReactNode
  code: string
}

interface PropDefinition {
  name: string
  type: string
  default?: string
  description: string
}

interface Foundation {
  id: string
  name: string
  description: string
  preview: React.ReactNode
}

// Categories using design system language
const CATEGORIES = [
  { id: 'foundations', name: 'Foundations', description: 'Design tokens, colors, typography, spacing' },
  { id: 'actions', name: 'Actions', description: 'Buttons, interactive elements' },
  { id: 'forms', name: 'Forms & Input', description: 'Text inputs, chat components' },
  { id: 'display', name: 'Display', description: 'Empty states, indicators, messaging' },
  { id: 'navigation', name: 'Navigation', description: 'Phase navigation, project switching' },
  { id: 'layout', name: 'Layout', description: 'Panels, containers, structure' },
]

// Foundation items (colors, typography, spacing, etc.)
const FOUNDATIONS: Foundation[] = [
  {
    id: 'colors',
    name: 'Color System',
    description: 'Semantic color tokens that adapt to light and dark modes - Click any color to edit',
    preview: <InteractiveColorSystem />,
  },
  {
    id: 'typography',
    name: 'Typography',
    description: 'Font families, sizes, and hierarchy - Click any font to change it',
    preview: <InteractiveTypographySystem />,
  },
  {
    id: 'spacing',
    name: 'Spacing System',
    description: '8px base unit spacing scale',
    preview: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
        {[
          { name: 'space-1', value: '4px' },
          { name: 'space-2', value: '8px' },
          { name: 'space-3', value: '12px' },
          { name: 'space-4', value: '16px' },
          { name: 'space-6', value: '24px' },
          { name: 'space-8', value: '32px' },
          { name: 'space-12', value: '48px' },
          { name: 'space-16', value: '64px' },
          { name: 'space-24', value: '96px' },
          { name: 'space-32', value: '128px' },
        ].map(space => (
          <div key={space.name} style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)' }}>
            <code className="code-text" style={{ fontSize: '13px', width: '120px', color: 'var(--text-muted)' }}>--{space.name}</code>
            <div style={{ fontSize: '13px', width: '60px', color: 'var(--text-muted)' }}>{space.value}</div>
            <div style={{ height: '32px', width: space.value, background: 'var(--accent)', borderRadius: 'var(--radius-sm)' }} />
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 'shadows',
    name: 'Elevation System',
    description: 'Shadow tokens for depth and hierarchy',
    preview: (
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: 'var(--space-6)' }}>
        {[
          { name: 'Panel', token: '--shadow-panel', desc: 'Floating panels' },
          { name: 'Elevated', token: '--shadow-elevated', desc: 'Dropdowns, popovers' },
          { name: 'Modal', token: '--shadow-modal', desc: 'Modal overlays' },
        ].map(shadow => (
          <div key={shadow.token} style={{ textAlign: 'center' }}>
            <div style={{
              width: '100%',
              height: '120px',
              background: 'var(--bg-primary)',
              borderRadius: 'var(--radius-lg)',
              marginBottom: 'var(--space-3)',
              boxShadow: `var(${shadow.token})`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              fontSize: '13px',
              fontWeight: 500
            }}>
              {shadow.name}
            </div>
            <code className="code-text" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{shadow.token}</code>
            <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: 'var(--space-1)' }}>{shadow.desc}</p>
          </div>
        ))}
      </div>
    ),
  },
  {
    id: 'motion',
    name: 'Motion System',
    description: 'Animation timing and easing for purposeful motion',
    preview: (
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
        {/* Animation Timing */}
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-3)', color: 'var(--text-muted)' }}>
            Animation Timing (Motion Protocol)
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
            {[
              { name: 'Instant', duration: '100ms', use: 'Hover states, instant feedback', token: '--animation-instant', example: 'Icon hover' },
              { name: 'Responsive', duration: '200ms', use: 'State changes, button presses', token: '--animation-responsive', example: 'Success checkmark' },
              { name: 'Deliberate', duration: '500ms', use: 'Loading, AI thinking', token: '--animation-deliberate', example: 'Spinner rotation' },
            ].map((timing, idx) => (
              <div key={timing.token} style={{ padding: 'var(--space-4)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
                  <div>
                    <div style={{ fontSize: '14px', fontWeight: 600 }}>{timing.name}</div>
                    <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>{timing.use}</div>
                  </div>
                  <code className="code-text" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{timing.duration}</code>
                </div>
                <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginBottom: 'var(--space-2)' }}>
                  Example: {timing.example}
                </div>
                <div style={{ height: '4px', background: 'var(--border)', borderRadius: '2px', overflow: 'hidden' }}>
                  <div
                    style={{
                      height: '100%',
                      width: '100%',
                      background: 'var(--accent)',
                      animation: `slideProgress${idx} ${timing.duration} cubic-bezier(0.4, 0, 0.2, 1) infinite`
                    }}
                  />
                </div>
                <style jsx>{`
                  @keyframes slideProgress${idx} {
                    0% { transform: translateX(-100%); }
                    50% { transform: translateX(0); }
                    100% { transform: translateX(0); }
                  }
                `}</style>
              </div>
            ))}
          </div>
        </div>

        {/* Easing Functions */}
        <div>
          <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-3)', color: 'var(--text-muted)' }}>
            Easing Functions
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            {[
              { name: 'Smooth', value: 'cubic-bezier(0.4, 0, 0.2, 1)', token: '--ease-smooth', use: 'Standard transitions' },
              { name: 'Spring', value: 'cubic-bezier(0.34, 1.56, 0.64, 1)', token: '--ease-spring', use: 'Energetic, bouncy' },
              { name: 'Gentle', value: 'ease-out', token: '--ease-gentle', use: 'Subtle deceleration' },
            ].map(easing => (
              <div key={easing.token} style={{ padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <div>
                  <div style={{ fontSize: '13px', fontWeight: 600 }}>{easing.name}</div>
                  <div style={{ fontSize: '11px', color: 'var(--text-muted)', marginTop: 'var(--space-1)' }}>{easing.use}</div>
                </div>
                <code className="code-text" style={{ fontSize: '10px', color: 'var(--text-muted)' }}>{easing.token}</code>
              </div>
            ))}
          </div>
        </div>

        {/* Link to Animated Icons */}
        <div style={{ padding: 'var(--space-4)', background: 'var(--color-success-bg)', border: '1px solid var(--color-success)', borderRadius: 'var(--radius-md)' }}>
          <div style={{ fontSize: '13px', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
            See Motion in Action
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-muted)' }}>
            Check out the <strong>Animated Icons</strong> section below to see these timing and easing values in use.
          </div>
        </div>
      </div>
    ),
  },
  {
    id: 'icons',
    name: 'Icon System',
    description: 'Complete icon library with SVG copy functionality. All icons built on 24×24 grid with 2px stroke.',
    preview: <IconGallery />,
  },
]

// Interactive Color System Component
function InteractiveColorSystem() {
  const [mounted, setMounted] = useState(false)
  const { colors, isInitialized, initializeFromCSS } = useColorStore()

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted && !isInitialized) {
      initializeFromCSS()
    }
  }, [mounted, isInitialized, initializeFromCSS])

  const colorDefinitions = [
    { token: 'background' as const, label: 'Background', desc: 'Canvas, page background' },
    { token: 'surface' as const, label: 'Surface', desc: 'Panel backgrounds' },
    { token: 'text' as const, label: 'Text Primary', desc: 'Primary text color' },
    { token: 'textMuted' as const, label: 'Text Muted', desc: 'Secondary text' },
    { token: 'border' as const, label: 'Border', desc: 'Default borders' },
    { token: 'primary' as const, label: 'Primary', desc: 'Brand primary' },
    { token: 'accent' as const, label: 'Accent', desc: 'Brand accent' },
    { token: 'success' as const, label: 'Success', desc: 'Success states' },
    { token: 'warning' as const, label: 'Attention', desc: 'Warning states' },
    { token: 'error' as const, label: 'Error', desc: 'Error states' },
  ]

  if (!mounted) {
    return (
      <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading interactive color system...
      </div>
    )
  }

  if (!isInitialized) {
    return (
      <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
        Initializing color system...
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Live Editing Info */}
      <div style={{
        padding: 'var(--space-4)',
        background: 'var(--color-success-bg)',
        border: '1px solid var(--color-success)',
        borderRadius: 'var(--radius-md)'
      }}>
        <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
          Live Color System
        </div>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Click any color to edit. Changes update instantly across the entire interface with AI-powered suggestions.
        </div>
      </div>

      {/* Color Editors Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: 'var(--space-4)'
      }}>
        {colorDefinitions.map(({ token, label, desc }) => (
          <ColorEditor
            key={token}
            colorToken={token}
            currentColor={colors[token]}
            label={label}
            description={desc}
          />
        ))}
      </div>
    </div>
  )
}

// Interactive Typography System Component
function InteractiveTypographySystem() {
  const [mounted, setMounted] = useState(false)
  const { fonts, isInitialized, initializeFromCSS } = useTypographyStore()

  useEffect(() => {
    setMounted(true)
  }, [])

  useEffect(() => {
    if (mounted && !isInitialized) {
      initializeFromCSS()
    }
  }, [mounted, isInitialized, initializeFromCSS])

  const fontDefinitions = [
    {
      token: 'heading' as const,
      label: 'Heading Font',
      desc: 'Headlines and section titles',
      sample: 'Design Intelligence'
    },
    {
      token: 'body' as const,
      label: 'Body Font',
      desc: 'Primary text content',
      sample: 'The quick brown fox jumps over the lazy dog'
    },
    {
      token: 'mono' as const,
      label: 'Monospace Font',
      desc: 'Code and technical text',
      sample: 'const font = "monospace";'
    },
  ]

  if (!mounted) {
    return (
      <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
        Loading interactive typography system...
      </div>
    )
  }

  if (!isInitialized) {
    return (
      <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--text-muted)' }}>
        Initializing typography system...
      </div>
    )
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Live Editing Info */}
      <div style={{
        padding: 'var(--space-4)',
        background: 'var(--color-success-bg)',
        border: '1px solid var(--color-success)',
        borderRadius: 'var(--radius-md)'
      }}>
        <div style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-1)' }}>
          Live Typography System
        </div>
        <div style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
          Click any font to change it. Preview fonts instantly and see changes across the entire interface.
        </div>
      </div>

      {/* Font Editors Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: 'var(--space-4)'
      }}>
        {fontDefinitions.map(({ token, label, desc, sample }) => (
          <FontEditor
            key={token}
            fontToken={token}
            currentFont={fonts[token]}
            label={label}
            description={desc}
            sampleText={sample}
          />
        ))}
      </div>

      {/* Type Scale Display */}
      <div style={{ marginTop: 'var(--space-4)' }}>
        <h3 style={{ fontSize: '14px', fontWeight: 600, marginBottom: 'var(--space-3)', color: 'var(--text-muted)' }}>
          Type Scale
        </h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
          {[
            { size: '54px', name: 'H1 - Hero', token: '--font-size-2xl' },
            { size: '36px', name: 'H2 - Page Title', token: '--font-size-xl' },
            { size: '24px', name: 'H3 - Section', token: '--font-size-lg' },
            { size: '16px', name: 'Body', token: '--font-size-base' },
            { size: '14px', name: 'Small', token: '--font-size-sm' },
            { size: '12px', name: 'Caption', token: '--font-size-xs' },
          ].map(type => (
            <div key={type.token} style={{ padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-md)', display: 'flex', alignItems: 'baseline', gap: 'var(--space-4)' }}>
              <div style={{ fontSize: type.size, fontFamily: 'var(--font-heading)', flex: '0 0 auto' }}>Aa</div>
              <div style={{ flex: 1 }}>
                <div style={{ fontSize: '13px', fontWeight: 600 }}>{type.name}</div>
                <code className="code-text" style={{ fontSize: '11px', color: 'var(--text-muted)' }}>{type.size} • {type.token}</code>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}

// Icon Gallery Component with copy functionality
function IconGallery() {
  const [copiedIcon, setCopiedIcon] = useState<string | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [showAnimated, setShowAnimated] = useState(false)
  const [hoveredIcon, setHoveredIcon] = useState<string | null>(null)

  // Define all icons with metadata
  const icons = [
    // Device Icons
    { name: 'DesktopIcon', component: DesktopIcon, category: 'Devices', description: 'Desktop computer' },
    { name: 'TabletIcon', component: TabletIcon, category: 'Devices', description: 'Tablet device' },
    { name: 'MobileIcon', component: MobileIcon, category: 'Devices', description: 'Mobile phone' },
    { name: 'WatchIcon', component: WatchIcon, category: 'Devices', description: 'Smart watch' },

    // Panel Icons
    { name: 'ConversationIcon', component: ConversationIcon, category: 'Panels', description: 'Chat conversation' },
    { name: 'HistoryIcon', component: HistoryIcon, category: 'Panels', description: 'History timeline' },
    { name: 'PropertiesIcon', component: PropertiesIcon, category: 'Panels', description: 'Settings properties' },
    { name: 'InspirationIcon', component: InspirationIcon, category: 'Panels', description: 'Image inspiration' },

    // Action Icons
    { name: 'PlusIcon', component: PlusIcon, category: 'Actions', description: 'Add new item' },
    { name: 'CloseIcon', component: CloseIcon, category: 'Actions', description: 'Close or dismiss' },
    { name: 'SendIcon', component: SendIcon, category: 'Actions', description: 'Send message' },
    { name: 'CheckIcon', component: CheckIcon, category: 'Actions', description: 'Confirm or complete' },
    { name: 'CopyIcon', component: CopyIcon, category: 'Actions', description: 'Copy to clipboard' },
    { name: 'UploadIcon', component: UploadIcon, category: 'Actions', description: 'Upload file' },

    // Navigation Icons
    { name: 'ChevronDownIcon', component: ChevronDownIcon, category: 'Navigation', description: 'Expand down' },
    { name: 'ChevronUpIcon', component: ChevronUpIcon, category: 'Navigation', description: 'Collapse up' },
    { name: 'ChevronLeftIcon', component: ChevronLeftIcon, category: 'Navigation', description: 'Navigate left' },
    { name: 'ChevronRightIcon', component: ChevronRightIcon, category: 'Navigation', description: 'Navigate right' },
    { name: 'ArrowRightIcon', component: ArrowRightIcon, category: 'Navigation', description: 'Go forward' },
    { name: 'HomeIcon', component: HomeIcon, category: 'Navigation', description: 'Home dashboard' },

    // State Icons
    { name: 'SparkleIcon', component: SparkleIcon, category: 'State', description: 'AI thinking' },
    { name: 'LoadingIcon', component: LoadingIcon, category: 'State', description: 'Loading spinner' },
    { name: 'AlertIcon', component: AlertIcon, category: 'State', description: 'Alert warning' },

    // File Icons
    { name: 'FileIcon', component: FileIcon, category: 'Files', description: 'Generic file' },
    { name: 'ImageIcon', component: ImageIcon, category: 'Files', description: 'Image file' },
    { name: 'ProjectIcon', component: ProjectIcon, category: 'Files', description: 'Project folder' },

    // Window Controls
    { name: 'MinimizeIcon', component: MinimizeIcon, category: 'Window', description: 'Minimize window' },
    { name: 'MaximizeIcon', component: MaximizeIcon, category: 'Window', description: 'Maximize window' },
    { name: 'DockTopLeftIcon', component: DockTopLeftIcon, category: 'Window', description: 'Dock top left' },
    { name: 'DockTopRightIcon', component: DockTopRightIcon, category: 'Window', description: 'Dock top right' },
    { name: 'DockBottomLeftIcon', component: DockBottomLeftIcon, category: 'Window', description: 'Dock bottom left' },
    { name: 'DockBottomRightIcon', component: DockBottomRightIcon, category: 'Window', description: 'Dock bottom right' },

    // Settings & Tools
    { name: 'SettingsIcon', component: SettingsIcon, category: 'Settings', description: 'Settings sliders' },
    { name: 'PencilIcon', component: PencilIcon, category: 'Settings', description: 'Edit or rename' },
    { name: 'SearchIcon', component: SearchIcon, category: 'Settings', description: 'Search' },

    // Phase Icons
    { name: 'GridIcon', component: GridIcon, category: 'Phases', description: 'Exploration grid' },
    { name: 'LayersIcon', component: LayersIcon, category: 'Phases', description: 'Expression layers' },
    { name: 'BoxIcon', component: BoxIcon, category: 'Phases', description: 'Delivery package' },

    // Communication
    { name: 'MessageCircleIcon', component: MessageCircleIcon, category: 'Communication', description: 'Message bubble' },

    // Theme
    { name: 'SunIcon', component: SunIcon, category: 'Theme', description: 'Light mode' },
    { name: 'MoonIcon', component: MoonIcon, category: 'Theme', description: 'Dark mode' },
  ]

  // Define animated icons with metadata
  const animatedIcons = [
    { name: 'AnimatedCheckIcon', component: AnimatedCheckIcon, staticName: 'CheckIcon', category: 'State Feedback', description: 'Success draw-in animation', timing: '300ms' },
    { name: 'AnimatedAlertIcon', component: AnimatedAlertIcon, staticName: 'AlertIcon', category: 'State Feedback', description: 'Warning pulse animation', timing: '200ms' },
    { name: 'AnimatedCopyIcon', component: AnimatedCopyIcon, staticName: 'CopyIcon', category: 'State Feedback', description: 'Confirmation bounce', timing: '100ms' },
    { name: 'AnimatedSendIcon', component: AnimatedSendIcon, staticName: 'SendIcon', category: 'State Feedback', description: 'Send action animation', timing: '200ms' },
    { name: 'AnimatedPlusIcon', component: AnimatedPlusIcon, staticName: 'PlusIcon', category: 'Interactive', description: 'Rotate on hover (90°)', timing: '100ms' },
    { name: 'AnimatedCloseIcon', component: AnimatedCloseIcon, staticName: 'CloseIcon', category: 'Interactive', description: 'Rotate on hover (45°)', timing: '100ms' },
    { name: 'AnimatedSunIcon', component: AnimatedSunIcon, staticName: 'SunIcon', category: 'Theme Toggle', description: 'Rotate + scale animation', timing: '300ms' },
    { name: 'AnimatedMoonIcon', component: AnimatedMoonIcon, staticName: 'MoonIcon', category: 'Theme Toggle', description: 'Scale + fade animation', timing: '300ms' },
    { name: 'AnimatedSparkleIcon', component: AnimatedSparkleIcon, staticName: 'SparkleIcon', category: 'Process', description: 'Continuous spin + pulse', timing: '500ms loop' },
    { name: 'AnimatedUploadIcon', component: AnimatedUploadIcon, staticName: 'UploadIcon', category: 'Process', description: 'Arrow bounce animation', timing: '300ms' },
    { name: 'AnimatedMaximizeIcon', component: AnimatedMaximizeIcon, staticName: 'MaximizeIcon', category: 'Panel Control', description: 'Scale from center', timing: '200ms' },
  ]

  // Use either static or animated icons based on toggle
  const iconsToDisplay = showAnimated ? animatedIcons : icons

  // Filter icons based on search
  const filteredIcons = iconsToDisplay.filter(icon =>
    icon.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
    icon.category.toLowerCase().includes(searchQuery.toLowerCase()) ||
    icon.description.toLowerCase().includes(searchQuery.toLowerCase())
  )

  // Group by category
  const groupedIcons = filteredIcons.reduce((acc, icon) => {
    if (!acc[icon.category]) {
      acc[icon.category] = []
    }
    acc[icon.category].push(icon)
    return acc
  }, {} as Record<string, typeof icons>)

  const copyIconSVG = async (iconName: string) => {
    // Generate SVG string from the icon
    const svgString = `<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" xmlns="http://www.w3.org/2000/svg">
  <!-- ${iconName} -->
</svg>`

    await navigator.clipboard.writeText(svgString)
    setCopiedIcon(iconName)
    setTimeout(() => setCopiedIcon(null), 2000)
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-6)' }}>
      {/* Animated/Static Toggle */}
      <div style={{ marginBottom: 'var(--space-4)' }}>
        <div style={{ display: 'inline-flex', background: 'var(--bg-secondary)', padding: '4px', borderRadius: 'var(--radius-md)', border: '1px solid var(--border)' }}>
          <button
            type="button"
            onClick={() => setShowAnimated(false)}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              fontSize: '13px',
              fontWeight: 500,
              background: !showAnimated ? 'var(--background)' : 'transparent',
              color: !showAnimated ? 'var(--text)' : 'var(--text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              transition: 'all 150ms',
            }}
          >
            Static Icons
          </button>
          <button
            type="button"
            onClick={() => setShowAnimated(true)}
            style={{
              padding: 'var(--space-2) var(--space-4)',
              fontSize: '13px',
              fontWeight: 500,
              background: showAnimated ? 'var(--background)' : 'transparent',
              color: showAnimated ? 'var(--text)' : 'var(--text-muted)',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              transition: 'all 150ms',
            }}
          >
            Animated Icons ✨
          </button>
        </div>
      </div>

      {/* Search Bar */}
      <div>
        <input
          type="text"
          className="studio-input"
          placeholder="Search icons by name, category, or description..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          style={{ width: '100%', maxWidth: '500px' }}
        />
        <p style={{ fontSize: '13px', color: 'var(--text-muted)', marginTop: 'var(--space-2)' }}>
          {filteredIcons.length} {filteredIcons.length === 1 ? 'icon' : 'icons'} available
        </p>
      </div>

      {/* Icon Grid by Category */}
      {Object.entries(groupedIcons).map(([category, categoryIcons]) => (
        <div key={category}>
          <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: 'var(--space-4)', color: 'var(--text)' }}>
            {category}
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(140px, 1fr))', gap: 'var(--space-3)' }}>
            {categoryIcons.map((icon) => {
              const IconComponent = icon.component as any
              const isCopied = copiedIcon === icon.name
              const isHovered = hoveredIcon === icon.name
              const isAnimated = showAnimated

              return (
                <button
                  key={icon.name}
                  type="button"
                  onClick={() => copyIconSVG(icon.name)}
                  style={{
                    display: 'flex',
                    flexDirection: 'column',
                    alignItems: 'center',
                    gap: 'var(--space-2)',
                    padding: 'var(--space-4)',
                    background: isCopied ? 'var(--color-success-bg)' : 'var(--bg-secondary)',
                    border: `1px solid ${isCopied ? 'var(--color-success)' : 'var(--border)'}`,
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    transition: 'all 150ms',
                    position: 'relative',
                  }}
                  onMouseEnter={(e) => {
                    setHoveredIcon(icon.name)
                    if (!isCopied) {
                      e.currentTarget.style.background = 'var(--color-hover)'
                      e.currentTarget.style.borderColor = 'var(--text-muted)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    setHoveredIcon(null)
                    if (!isCopied) {
                      e.currentTarget.style.background = 'var(--bg-secondary)'
                      e.currentTarget.style.borderColor = 'var(--border)'
                    }
                  }}
                  title={`${icon.description} - Click to copy SVG`}
                  aria-label={`Copy ${icon.name} SVG`}
                >
                  {isAnimated ? (
                    <IconComponent
                      size={24}
                      color={isCopied ? 'var(--color-success)' : 'var(--text)'}
                      isActive={isHovered}
                    />
                  ) : (
                    <IconComponent
                      size={24}
                      color={isCopied ? 'var(--color-success)' : 'var(--text)'}
                    />
                  )}
                  <div style={{ textAlign: 'center' }}>
                    <div className="code-text" style={{ fontSize: '11px', fontWeight: 500, marginBottom: 'var(--space-1)' }}>
                      {icon.name.replace('Icon', '').replace('Animated', '')}
                    </div>
                    <div style={{ fontSize: '10px', color: 'var(--text-muted)' }}>
                      {isCopied ? 'Copied!' : 'Click to copy'}
                    </div>
                    {showAnimated && (icon as any).timing && (
                      <div style={{ fontSize: '10px', color: 'var(--accent)', marginTop: 'var(--space-1)' }}>
                        {(icon as any).timing}
                      </div>
                    )}
                  </div>
                </button>
              )
            })}
          </div>
        </div>
      ))}

      {filteredIcons.length === 0 && (
        <div style={{
          padding: 'var(--space-12)',
          textAlign: 'center',
          color: 'var(--text-muted)',
          fontSize: '14px'
        }}>
          No icons found matching &quot;{searchQuery}&quot;
        </div>
      )}

      {/* Usage Guide */}
      <div className="studio-panel" style={{ padding: 'var(--space-6)', borderRadius: 'var(--radius-lg)', marginTop: 'var(--space-8)' }}>
        <h3 style={{ fontSize: '16px', fontWeight: 600, marginBottom: 'var(--space-4)' }}>Usage</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
          {showAnimated ? (
            <div>
              <code className="code-text" style={{ fontSize: '13px', display: 'block', marginBottom: 'var(--space-2)' }}>
                import {'{AnimatedCheckIcon}'} from &apos;@/components/icons/animated&apos;
              </code>
              <code className="code-text" style={{ fontSize: '13px', display: 'block', marginBottom: 'var(--space-3)' }}>
                {`<AnimatedCheckIcon size={24} isActive={true} color="var(--text)" />`}
              </code>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                <strong>Props (extends IconProps):</strong>
                <ul style={{ marginTop: 'var(--space-2)', paddingLeft: 'var(--space-4)' }}>
                  <li><code className="code-text">isActive</code> - Boolean to trigger animation</li>
                  <li><code className="code-text">animationSpeed</code> - Number (0.5-2x multiplier, default: 1)</li>
                  <li><code className="code-text">onAnimationComplete</code> - Callback function</li>
                  <li><code className="code-text">size, color, strokeWidth, className</code> - Standard icon props</li>
                </ul>
                <div style={{ marginTop: 'var(--space-3)', padding: 'var(--space-3)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-sm)' }}>
                  <strong>Accessibility:</strong> All animations respect <code className="code-text">prefers-reduced-motion</code>
                </div>
              </div>
            </div>
          ) : (
            <div>
              <code className="code-text" style={{ fontSize: '13px', display: 'block', marginBottom: 'var(--space-2)' }}>
                import {'{CheckIcon}'} from &apos;@/components/icons/Icon&apos;
              </code>
              <code className="code-text" style={{ fontSize: '13px', display: 'block' }}>
                {`<CheckIcon size={24} color="var(--text)" strokeWidth={2} />`}
              </code>
              <div style={{ fontSize: '13px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                <strong>Props:</strong>
                <ul style={{ marginTop: 'var(--space-2)', paddingLeft: 'var(--space-4)' }}>
                  <li><code className="code-text">size</code> - Number or string (default: 24)</li>
                  <li><code className="code-text">color</code> - CSS color value (default: currentColor)</li>
                  <li><code className="code-text">strokeWidth</code> - Number (default: 2)</li>
                  <li><code className="code-text">className</code> - Additional CSS classes</li>
                </ul>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

// Component definitions
const COMPONENTS: Component[] = [
  // ACTIONS CATEGORY
  {
    id: 'button',
    name: 'Button',
    category: 'actions',
    description: 'Trigger actions and navigate your interface',
    variants: [
      {
        name: 'Primary',
        preview: <button className="studio-button studio-button-primary">Primary Button</button>,
        code: '<button className="studio-button studio-button-primary">Primary Button</button>'
      },
      {
        name: 'Secondary',
        preview: <button className="studio-button studio-button-secondary">Secondary Button</button>,
        code: '<button className="studio-button studio-button-secondary">Secondary Button</button>'
      },
      {
        name: 'Ghost',
        preview: <button className="studio-button studio-button-ghost">Ghost Button</button>,
        code: '<button className="studio-button studio-button-ghost">Ghost Button</button>'
      },
      {
        name: 'Sizes',
        preview: (
          <div style={{ display: 'flex', gap: 'var(--space-3)', alignItems: 'center' }}>
            <button className="studio-button studio-button-primary studio-button-sm">Small</button>
            <button className="studio-button studio-button-primary">Medium</button>
            <button className="studio-button studio-button-primary studio-button-lg">Large</button>
          </div>
        ),
        code: `<button className="studio-button studio-button-primary studio-button-sm">Small</button>
<button className="studio-button studio-button-primary">Medium</button>
<button className="studio-button studio-button-primary studio-button-lg">Large</button>`
      },
      {
        name: 'With Icon',
        preview: (
          <button className="studio-button studio-button-primary" style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
            <span>Continue</span>
            <ArrowRightIcon size={16} />
          </button>
        ),
        code: `<button className="studio-button studio-button-primary">
  <span>Continue</span>
  <ArrowRightIcon size={16} />
</button>`
      },
      {
        name: 'Icon Only',
        preview: (
          <div style={{ display: 'flex', gap: 'var(--space-2)' }}>
            <button className="studio-button-icon"><CheckIcon size={18} /></button>
            <button className="studio-button-icon"><HomeIcon size={18} /></button>
            <button className="studio-button-icon"><PencilIcon size={18} /></button>
          </div>
        ),
        code: `<button className="studio-button-icon">
  <CheckIcon size={18} />
</button>`
      }
    ],
    props: [
      { name: 'className', type: 'string', description: 'Base: studio-button, Variants: studio-button-primary | studio-button-secondary | studio-button-ghost' },
      { name: 'size', type: 'string', description: 'Add studio-button-sm or studio-button-lg for sizes' },
      { name: 'disabled', type: 'boolean', default: 'false', description: 'Disabled state' },
    ],
    code: `// Import (if using component version)
import { Button } from '@/components/Button'

// Usage with CSS classes (recommended)
<button className="studio-button studio-button-primary">
  Click me
</button>

// With icon
<button className="studio-button studio-button-primary">
  <span>Continue</span>
  <ArrowRightIcon size={16} />
</button>`,
    accessibility: [
      'Native button element for proper keyboard support',
      'Enter and Space keys trigger click',
      'Focus visible with outline',
      'Disabled state prevents interaction and is announced to screen readers',
      'Minimum touch target 44x44px (Apple) or 48x48dp (Android)',
    ]
  },

  // FORMS & INPUT CATEGORY
  {
    id: 'input',
    name: 'Input',
    category: 'forms',
    description: 'Text input fields with Studio styling',
    variants: [
      {
        name: 'Default',
        preview: <input className="studio-input" placeholder="Enter text..." />,
        code: '<input className="studio-input" placeholder="Enter text..." />'
      },
      {
        name: 'Focused',
        preview: <input className="studio-input" placeholder="Focused state" autoFocus />,
        code: '<input className="studio-input" placeholder="Focused state" />'
      },
    ],
    props: [
      { name: 'className', type: 'string', description: 'Use studio-input for consistent styling' },
      { name: 'type', type: 'string', default: 'text', description: 'Input type (text, email, password, etc.)' },
      { name: 'placeholder', type: 'string', description: 'Placeholder text' },
    ],
    code: `// Basic input
<input
  className="studio-input"
  type="text"
  placeholder="Enter text..."
/>

// With label
<label>
  <span>Project Name</span>
  <input className="studio-input" type="text" />
</label>`,
    accessibility: [
      'Always pair with a label (visible or aria-label)',
      'Placeholder is not a substitute for label',
      'Focus state clearly visible',
      'Minimum height 44px for touch targets',
    ]
  },
  {
    id: 'chat-input',
    name: 'ChatInput',
    category: 'forms',
    description: 'Auto-growing textarea with send button for chat interfaces',
    variants: [
      {
        name: 'Default',
        preview: (
          <div style={{ width: '100%', maxWidth: '600px' }}>
            <ChatInput onSend={(msg) => console.log(msg)} placeholder="Type a message..." />
          </div>
        ),
        code: '<ChatInput onSend={(msg) => console.log(msg)} placeholder="Type a message..." />'
      },
      {
        name: 'With Suggestions',
        preview: (
          <div style={{ width: '100%', maxWidth: '600px' }}>
            <ChatInput
              onSend={(msg) => console.log(msg)}
              placeholder="Ask a question..."
              suggestedQuestions={['What is Studio?', 'How do I start?', 'Show me examples']}
            />
          </div>
        ),
        code: `<ChatInput
  onSend={(msg) => console.log(msg)}
  suggestedQuestions={['What is Studio?', 'How do I start?']}
/>`
      },
    ],
    props: [
      { name: 'onSend', type: '(message: string) => void', description: 'Callback when message is sent' },
      { name: 'placeholder', type: 'string', default: 'Type a message...', description: 'Placeholder text' },
      { name: 'disabled', type: 'boolean', default: 'false', description: 'Disable input' },
      { name: 'suggestedQuestions', type: 'string[]', default: '[]', description: 'Suggested questions shown when empty' },
      { name: 'accentColor', type: 'string', default: 'var(--accent)', description: 'Custom accent color' },
    ],
    code: `import { ChatInput } from '@/components/chat/ChatInput'

<ChatInput
  onSend={(message) => {
    // Handle message
  }}
  placeholder="Ask me anything..."
  suggestedQuestions={[
    'What is Studio?',
    'How do I start?',
    'Show me examples'
  ]}
/>`,
    accessibility: [
      'Auto-growing textarea adapts to content',
      'Enter to send, Shift+Enter for new line',
      'Send button disabled when empty',
      'Keyboard navigation fully supported',
      'Screen reader announces send button state',
    ]
  },

  // DISPLAY CATEGORY
  {
    id: 'typing-indicator',
    name: 'TypingIndicator',
    category: 'display',
    description: 'Animated dots showing AI is thinking',
    variants: [
      {
        name: 'Default',
        preview: <TypingIndicator />,
        code: '<TypingIndicator />'
      },
      {
        name: 'Custom Color',
        preview: <TypingIndicator accentColor="var(--primary)" />,
        code: '<TypingIndicator accentColor="var(--primary)" />'
      },
    ],
    props: [
      { name: 'accentColor', type: 'string', default: 'var(--accent)', description: 'Color of animated dots' },
    ],
    code: `import { TypingIndicator } from '@/components/chat/TypingIndicator'

// Default
<TypingIndicator />

// Custom color
<TypingIndicator accentColor="var(--primary)" />`,
    accessibility: [
      'Communicates AI is processing',
      'Animation follows motion timing protocol',
      'Respects prefers-reduced-motion',
    ]
  },
  {
    id: 'empty-state',
    name: 'EmptyState',
    category: 'display',
    description: 'Welcome screen with interactive background and playful hover states',
    variants: [
      {
        name: 'Preview',
        preview: (
          <div style={{ width: '100%', height: '400px', background: 'var(--background)', borderRadius: 'var(--radius-lg)', display: 'flex', alignItems: 'center', justifyContent: 'center', position: 'relative', overflow: 'hidden' }}>
            <div style={{ textAlign: 'center', padding: 'var(--space-6)' }}>
              <h1 className="font-heading" style={{ fontSize: '36px', fontWeight: 700, marginBottom: 'var(--space-4)' }}>
                Welcome to <span style={{ color: 'var(--accent)' }}>Studio</span>
              </h1>
              <p style={{ fontSize: '16px', color: 'var(--text-muted)', marginBottom: 'var(--space-6)' }}>
                Your design partner that transforms intent into expression
              </p>
              <button className="studio-button studio-button-primary studio-button-lg">
                Start New Project
              </button>
            </div>
          </div>
        ),
        code: '<EmptyState />'
      },
    ],
    props: [],
    code: `import { EmptyState } from '@/components/EmptyState'

// Full-screen welcome experience
<EmptyState />

// Features:
// - Interactive gradient follows mouse
// - Playful color palettes on hover
// - Letter cascade animation
// - Auth modal integration`,
    accessibility: [
      'Clear call-to-action button',
      'Keyboard accessible',
      'Motion respects user preferences',
      'High contrast text on all backgrounds',
    ]
  },

  // NAVIGATION CATEGORY
  {
    id: 'phase-navigator',
    name: 'PhaseNavigator',
    category: 'navigation',
    description: 'Four-phase progression indicator with visual states',
    variants: [
      {
        name: 'Interactive',
        preview: (
          <div style={{ padding: 'var(--space-4)', background: 'var(--bg-secondary)', borderRadius: 'var(--radius-lg)' }}>
            <PhaseNavigator />
          </div>
        ),
        code: '<PhaseNavigator />'
      },
    ],
    props: [],
    code: `import { PhaseNavigator } from '@/components/PhaseNavigator'

// Connects to Zustand store for state
<PhaseNavigator />

// Phases: Discover → Explore → Express → Create
// Features:
// - Progressive unlock
// - Visual completion indicators
// - Smooth transitions
// - Connected dots show progress`,
    accessibility: [
      'Keyboard navigable',
      'Clear visual states (current, complete, locked)',
      'Button disabled state properly announced',
      'Touch targets meet minimum size',
    ]
  },
]

export function ComponentShowcase() {
  const [selectedCategory, setSelectedCategory] = useState('foundations')
  const [selectedComponent, setSelectedComponent] = useState<Component | null>(null)
  const [selectedFoundation, setSelectedFoundation] = useState<Foundation | null>(FOUNDATIONS[0])
  const [activeTab, setActiveTab] = useState<'preview' | 'code' | 'props'>('preview')
  const [copiedCode, setCopiedCode] = useState(false)
  const [theme, setTheme] = useState<'light' | 'dark'>('light')
  const [isInitialized, setIsInitialized] = useState(false)

  const filteredComponents = COMPONENTS.filter(c => c.category === selectedCategory)
  const isFoundationsCategory = selectedCategory === 'foundations'

  // Initialize theme from document on mount
  useEffect(() => {
    const currentTheme = document.documentElement.getAttribute('data-theme')
    if (currentTheme === 'dark' || currentTheme === 'light') {
      setTheme(currentTheme)
    } else {
      // No theme set, default to light
      document.documentElement.setAttribute('data-theme', 'light')
    }
    setIsInitialized(true)
  }, [])

  // Apply theme to document when it changes (smooth transition handled by CSS)
  useEffect(() => {
    if (isInitialized) {
      document.documentElement.setAttribute('data-theme', theme)
    }
  }, [theme, isInitialized])

  const toggleTheme = () => {
    setTheme(current => current === 'light' ? 'dark' : 'light')
  }

  // Show the CURRENT mode icon (sun = light mode, moon = dark mode)
  const getThemeIcon = () => {
    return theme === 'light' ? <SunIcon size={18} /> : <MoonIcon size={18} />
  }

  const handleCopyCode = () => {
    const code = selectedComponent?.code
    if (code) {
      navigator.clipboard.writeText(code)
      setCopiedCode(true)
      setTimeout(() => setCopiedCode(false), 2000)
    }
  }

  const handleCategoryChange = (categoryId: string) => {
    setSelectedCategory(categoryId)
    if (categoryId === 'foundations') {
      setSelectedFoundation(FOUNDATIONS[0])
      setSelectedComponent(null)
    } else {
      const firstComponent = COMPONENTS.find(c => c.category === categoryId)
      setSelectedComponent(firstComponent || null)
      setSelectedFoundation(null)
    }
    setActiveTab('preview')
  }

  return (
    <div className="flex h-full w-full" style={{ background: 'var(--background)' }}>
      {/* Sidebar - Categories & Components */}
      <div
        className="studio-panel border-r flex flex-col"
        style={{
          width: '280px',
          borderRight: '1px solid var(--border)',
          overflow: 'hidden'
        }}
      >
        {/* Header */}
        <div style={{ padding: 'var(--space-6) var(--space-5)', borderBottom: '1px solid var(--border)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-2)' }}>
            <h2 className="font-heading" style={{ fontSize: '18px', fontWeight: 600 }}>
              Design System
            </h2>
            {/* Theme Switcher */}
            <button
              type="button"
              onClick={toggleTheme}
              className="studio-button-icon"
              style={{
                width: '32px',
                height: '32px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              title={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
              aria-label={`Switch to ${theme === 'light' ? 'dark' : 'light'} mode`}
            >
              {getThemeIcon()}
            </button>
          </div>
          <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Components • Tokens • Patterns
          </p>
        </div>

        {/* Categories */}
        <div style={{ overflowY: 'auto', flex: 1 }}>
          <div style={{ padding: 'var(--space-3) var(--space-2)' }}>
            <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', padding: 'var(--space-2) var(--space-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
              Categories
            </div>
            {CATEGORIES.map(category => (
              <button
                key={category.id}
                onClick={() => handleCategoryChange(category.id)}
                className="w-full"
                style={{
                  display: 'flex',
                  flexDirection: 'column',
                  alignItems: 'flex-start',
                  gap: 'var(--space-1)',
                  padding: 'var(--space-2-5) var(--space-3)',
                  fontSize: '14px',
                  textAlign: 'left',
                  border: 'none',
                  background: selectedCategory === category.id ? 'var(--color-hover)' : 'transparent',
                  color: selectedCategory === category.id ? 'var(--text)' : 'var(--text-muted)',
                  borderRadius: 'var(--radius-md)',
                  cursor: 'pointer',
                  transition: 'all 150ms',
                  fontWeight: selectedCategory === category.id ? 500 : 400
                }}
                onMouseEnter={(e) => {
                  if (selectedCategory !== category.id) {
                    e.currentTarget.style.background = 'var(--color-hover)'
                  }
                }}
                onMouseLeave={(e) => {
                  if (selectedCategory !== category.id) {
                    e.currentTarget.style.background = 'transparent'
                  }
                }}
              >
                <span>{category.name}</span>
                <span style={{ fontSize: '11px', opacity: 0.7 }}>{category.description}</span>
              </button>
            ))}
          </div>

          {/* Component/Foundation List */}
          {isFoundationsCategory ? (
            <div style={{ padding: 'var(--space-3) var(--space-2)', borderTop: '1px solid var(--border)' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', padding: 'var(--space-2) var(--space-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Foundations
              </div>
              {FOUNDATIONS.map(foundation => (
                <button
                  key={foundation.id}
                  onClick={() => {
                    setSelectedFoundation(foundation)
                    setSelectedComponent(null)
                  }}
                  className="w-full"
                  style={{
                    display: 'block',
                    padding: 'var(--space-2-5) var(--space-3)',
                    fontSize: '14px',
                    textAlign: 'left',
                    border: 'none',
                    background: selectedFoundation?.id === foundation.id ? 'var(--color-hover)' : 'transparent',
                    color: selectedFoundation?.id === foundation.id ? 'var(--text)' : 'var(--text-muted)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    transition: 'all 150ms',
                    fontWeight: selectedFoundation?.id === foundation.id ? 500 : 400
                  }}
                  onMouseEnter={(e) => {
                    if (selectedFoundation?.id !== foundation.id) {
                      e.currentTarget.style.background = 'var(--color-hover)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedFoundation?.id !== foundation.id) {
                      e.currentTarget.style.background = 'transparent'
                    }
                  }}
                >
                  {foundation.name}
                </button>
              ))}
            </div>
          ) : filteredComponents.length > 0 ? (
            <div style={{ padding: 'var(--space-3) var(--space-2)', borderTop: '1px solid var(--border)' }}>
              <div style={{ fontSize: '11px', fontWeight: 600, color: 'var(--text-muted)', padding: 'var(--space-2) var(--space-3)', textTransform: 'uppercase', letterSpacing: '0.05em' }}>
                Components
              </div>
              {filteredComponents.map(component => (
                <button
                  key={component.id}
                  onClick={() => {
                    setSelectedComponent(component)
                    setSelectedFoundation(null)
                    setActiveTab('preview')
                  }}
                  className="w-full"
                  style={{
                    display: 'block',
                    padding: 'var(--space-2-5) var(--space-3)',
                    fontSize: '14px',
                    textAlign: 'left',
                    border: 'none',
                    background: selectedComponent?.id === component.id ? 'var(--color-hover)' : 'transparent',
                    color: selectedComponent?.id === component.id ? 'var(--text)' : 'var(--text-muted)',
                    borderRadius: 'var(--radius-md)',
                    cursor: 'pointer',
                    transition: 'all 150ms',
                    fontWeight: selectedComponent?.id === component.id ? 500 : 400
                  }}
                  onMouseEnter={(e) => {
                    if (selectedComponent?.id !== component.id) {
                      e.currentTarget.style.background = 'var(--color-hover)'
                    }
                  }}
                  onMouseLeave={(e) => {
                    if (selectedComponent?.id !== component.id) {
                      e.currentTarget.style.background = 'transparent'
                    }
                  }}
                >
                  {component.name}
                </button>
              ))}
            </div>
          ) : null}
        </div>
      </div>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col" style={{ overflow: 'hidden' }}>
        {selectedFoundation ? (
          <>
            {/* Foundation Header */}
            <div style={{ padding: 'var(--space-8) var(--space-12)', borderBottom: '1px solid var(--border)' }}>
              <h1 className="font-heading" style={{ fontSize: '36px', fontWeight: 700, marginBottom: 'var(--space-3)', letterSpacing: '-0.02em' }}>
                {selectedFoundation.name}
              </h1>
              <p style={{ fontSize: '16px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                {selectedFoundation.description}
              </p>
            </div>

            {/* Foundation Content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-12)' }}>
              {selectedFoundation.preview}
            </div>
          </>
        ) : selectedComponent ? (
          <>
            {/* Component Header */}
            <div style={{ padding: 'var(--space-8) var(--space-12)', borderBottom: '1px solid var(--border)' }}>
              <h1 className="font-heading" style={{ fontSize: '36px', fontWeight: 700, marginBottom: 'var(--space-3)', letterSpacing: '-0.02em' }}>
                {selectedComponent.name}
              </h1>
              <p style={{ fontSize: '16px', color: 'var(--text-muted)', lineHeight: '1.6' }}>
                {selectedComponent.description}
              </p>
            </div>

            {/* Tabs */}
            <div style={{ borderBottom: '1px solid var(--border)', padding: '0 var(--space-12)' }}>
              <div style={{ display: 'flex', gap: 'var(--space-8)' }}>
                {(['preview', 'code', 'props'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    style={{
                      padding: 'var(--space-4) 0',
                      fontSize: '14px',
                      fontWeight: 500,
                      border: 'none',
                      background: 'none',
                      color: activeTab === tab ? 'var(--text)' : 'var(--text-muted)',
                      borderBottom: activeTab === tab ? '2px solid var(--text)' : '2px solid transparent',
                      cursor: 'pointer',
                      transition: 'all 150ms',
                      textTransform: 'capitalize'
                    }}
                  >
                    {tab}
                  </button>
                ))}
              </div>
            </div>

            {/* Tab Content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 'var(--space-12)' }}>
              {activeTab === 'preview' && (
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: 'var(--space-6)' }}>Variants</h3>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-8)' }}>
                    {selectedComponent.variants.map((variant, idx) => (
                      <div key={idx} className="studio-panel" style={{ padding: 'var(--space-8)', borderRadius: 'var(--radius-lg)' }}>
                        <div style={{ fontSize: '14px', fontWeight: 500, marginBottom: 'var(--space-5)', color: 'var(--text-muted)' }}>
                          {variant.name}
                        </div>
                        <div style={{ marginBottom: 'var(--space-5)' }}>
                          {variant.preview}
                        </div>
                        <div style={{
                          background: 'var(--surface-muted)',
                          padding: 'var(--space-4) var(--space-5)',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--border)',
                          overflow: 'auto'
                        }}>
                          <pre className="code-block font-mono" style={{
                            margin: 0,
                            whiteSpace: 'pre-wrap',
                            fontSize: '13px',
                            lineHeight: '1.5',
                            color: 'var(--text)'
                          }}><code className="code-text">{variant.code}</code></pre>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}

              {activeTab === 'code' && (
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 'var(--space-6)' }}>
                    <h3 style={{ fontSize: '18px', fontWeight: 600 }}>Usage</h3>
                    <button
                      className="studio-button studio-button-secondary"
                      onClick={handleCopyCode}
                    >
                      {copiedCode ? 'Copied!' : 'Copy Code'}
                    </button>
                  </div>
                  <div className="studio-panel" style={{
                    background: 'var(--surface-muted)',
                    padding: 'var(--space-6)',
                    borderRadius: 'var(--radius-lg)',
                    border: '1px solid var(--border)',
                    overflowX: 'auto'
                  }}>
                    <pre className="code-block font-mono" style={{
                      margin: 0,
                      fontSize: '14px',
                      lineHeight: '1.6',
                      color: 'var(--text)',
                      whiteSpace: 'pre-wrap',
                      wordBreak: 'break-word'
                    }}>
                      <code className="code-text">{selectedComponent.code}</code>
                    </pre>
                  </div>
                </div>
              )}

              {activeTab === 'props' && (
                <div>
                  <h3 style={{ fontSize: '18px', fontWeight: 600, marginBottom: 'var(--space-6)' }}>Props</h3>
                  <div className="studio-panel" style={{ padding: 'var(--space-6)', borderRadius: 'var(--radius-lg)', overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--border)' }}>
                          <th style={{ padding: 'var(--space-3) var(--space-4) var(--space-3) 0', textAlign: 'left', fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>Name</th>
                          <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'left', fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>Type</th>
                          <th style={{ padding: 'var(--space-3) var(--space-4)', textAlign: 'left', fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>Default</th>
                          <th style={{ padding: 'var(--space-3) 0 var(--space-3) var(--space-4)', textAlign: 'left', fontSize: '13px', fontWeight: 600, color: 'var(--text-muted)' }}>Description</th>
                        </tr>
                      </thead>
                      <tbody>
                        {selectedComponent.props.map((prop, idx) => (
                          <tr key={idx} style={{ borderBottom: idx < selectedComponent.props.length - 1 ? '1px solid var(--border)' : 'none' }}>
                            <td className="code-text" style={{ padding: 'var(--space-4) var(--space-4) var(--space-4) 0', fontSize: '14px' }}>{prop.name}</td>
                            <td className="code-text" style={{ padding: 'var(--space-4)', fontSize: '13px', color: 'var(--text-muted)' }}>{prop.type}</td>
                            <td className="code-text" style={{ padding: 'var(--space-4)', fontSize: '13px', color: 'var(--text-muted)' }}>{prop.default || '-'}</td>
                            <td style={{ padding: 'var(--space-4) 0 var(--space-4) var(--space-4)', fontSize: '14px', color: 'var(--text-muted)' }}>{prop.description}</td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>

                  <h3 style={{ fontSize: '18px', fontWeight: 600, marginTop: 'var(--space-12)', marginBottom: 'var(--space-6)' }}>Accessibility</h3>
                  <div className="studio-panel" style={{ padding: 'var(--space-6)', borderRadius: 'var(--radius-lg)' }}>
                    <ul style={{ margin: 0, padding: 0, listStyle: 'none' }}>
                      {selectedComponent.accessibility.map((item, idx) => (
                        <li key={idx} style={{
                          display: 'flex',
                          alignItems: 'flex-start',
                          gap: 'var(--space-3)',
                          marginBottom: idx < selectedComponent.accessibility.length - 1 ? 'var(--space-4)' : 0,
                          fontSize: '14px',
                          lineHeight: '1.6'
                        }}>
                          <span style={{ flexShrink: 0, marginTop: '2px' }}>
                            <CheckIcon size={16} color="var(--color-success)" />
                          </span>
                          {item}
                        </li>
                      ))}
                    </ul>
                  </div>
                </div>
              )}
            </div>
          </>
        ) : (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            height: '100%',
            color: 'var(--text-muted)',
            fontSize: '16px'
          }}>
            Select a component or foundation to view details
          </div>
        )}
      </div>
    </div>
  )
}
