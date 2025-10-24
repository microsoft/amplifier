'use client'

import { useState } from 'react'
import { useStudioStore } from '@/state/store'
import {
  ConversationIcon,
  HistoryIcon,
  DesktopIcon,
  TabletIcon,
  MobileIcon,
  WatchIcon,
} from '@/components/icons/Icon'
import { ComponentShowcase } from './ComponentShowcase'

/**
 * Expression Workspace - Full design workspace
 * Canvas + tools for refining generated designs
 * Aesthetic: German car facility - clean, precise, beautiful
 */

type WorkspaceMode = 'canvas' | 'components' | 'blocks' | 'charts'

export function ExpressionWorkspace() {
  const { panels, togglePanel, devicePreview } = useStudioStore()
  const [workspaceMode, setWorkspaceMode] = useState<WorkspaceMode>('components')

  const deviceIcons = {
    desktop: DesktopIcon,
    tablet: TabletIcon,
    mobile: MobileIcon,
    watch: WatchIcon,
  }

  const devices = ['desktop', 'tablet', 'mobile', 'watch'] as const

  return (
    <div className="flex h-screen w-screen overflow-hidden studio-canvas">
      {/* Main Canvas Area */}
      <main className="flex-1 flex flex-col">
        {/* Toolbar - Dimension 1 & 8: Frosted glass */}
        <div className="studio-toolbar flex items-center justify-between" style={{ height: 'var(--toolbar-height)' }}>
          {/* Left: Brand */}
          <div className="flex items-center gap-3 px-6">
            <h1 className="font-heading" style={{ fontSize: '20px', fontWeight: 600, letterSpacing: '-0.01em' }}>
              Studio
            </h1>
            <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Design Intelligence
            </span>
          </div>

          {/* Center: Mode Switcher */}
          <div className="flex items-center gap-1">
            {(['components', 'blocks', 'charts', 'canvas'] as const).map((mode) => (
              <button
                key={mode}
                className={`studio-button studio-button-sm ${
                  workspaceMode === mode
                    ? 'studio-button-primary'
                    : 'studio-button-ghost'
                }`}
                onClick={() => setWorkspaceMode(mode)}
                style={{ textTransform: 'capitalize' }}
              >
                {mode}
              </button>
            ))}
          </div>

          {/* Right: Panel Toggles */}
          <div className="flex items-center gap-2 px-6">
            {workspaceMode === 'canvas' && (
              <div className="device-switcher-container" style={{ marginRight: '16px' }}>
                <div
                  className="device-switcher-indicator"
                  style={{
                    transform: `translateX(${devices.indexOf(devicePreview) * 44}px)`,
                    width: '40px'
                  }}
                />
                {devices.map((device) => {
                  const IconComponent = deviceIcons[device]
                  return (
                    <button
                      key={device}
                      className={`device-switcher-button ${devicePreview === device ? 'active' : ''}`}
                      onClick={() => useStudioStore.setState({ devicePreview: device })}
                      title={device.charAt(0).toUpperCase() + device.slice(1)}
                    >
                      <IconComponent size={18} />
                    </button>
                  )
                })}
              </div>
            )}
            <button
              className={`studio-button studio-button-sm ${
                panels.conversation
                  ? 'studio-button-primary'
                  : 'studio-button-secondary'
              }`}
              onClick={() => togglePanel('conversation')}
            >
              <ConversationIcon size={16} />
              <span>Conversation</span>
            </button>
            <button
              className={`studio-button studio-button-sm ${
                panels.history
                  ? 'studio-button-primary'
                  : 'studio-button-secondary'
              }`}
              onClick={() => togglePanel('history')}
            >
              <HistoryIcon size={16} />
              <span>History</span>
            </button>
          </div>
        </div>

        {/* Main Content Area - Switch based on mode */}
        <div className="flex-1 flex" style={{ overflow: 'hidden' }}>
          {workspaceMode === 'components' && <ComponentShowcase />}

          {workspaceMode === 'blocks' && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <h2 className="font-heading" style={{ fontSize: '28px', fontWeight: 600, marginBottom: '16px' }}>
                  Blocks
                </h2>
                <p style={{ fontSize: '16px', color: 'var(--text-muted)' }}>
                  Pre-composed patterns coming soon
                </p>
              </div>
            </div>
          )}

          {workspaceMode === 'charts' && (
            <div className="flex-1 flex items-center justify-center">
              <div className="text-center">
                <h2 className="font-heading" style={{ fontSize: '28px', fontWeight: 600, marginBottom: '16px' }}>
                  Charts
                </h2>
                <p style={{ fontSize: '16px', color: 'var(--text-muted)' }}>
                  Data visualization components coming soon
                </p>
              </div>
            </div>
          )}

          {workspaceMode === 'canvas' && (
            <div className="flex-1 flex items-center justify-center" style={{ padding: '64px' }}>
              {/* Welcome Panel - Dimension 1 & 8: Frosted panel with elevation */}
              <div className="studio-panel rounded-lg text-center fade-in" style={{ padding: '48px', maxWidth: '560px' }}>
                <h2 className="font-heading" style={{ fontSize: '28px', fontWeight: 600, marginBottom: '16px' }}>
                  Canvas Mode
                </h2>
                <p style={{ fontSize: '16px', lineHeight: '1.6', color: 'var(--text-muted)', marginBottom: '32px' }}>
                  Device preview and live design editing coming soon
                </p>
                <button className="studio-button studio-button-primary studio-button-lg">
                  Start Designing
                </button>
              </div>
            </div>
          )}
        </div>

        {/* History Timeline - Dimension 2: Slide animation */}
        <div
          className="studio-panel border-t"
          style={{
            height: 'var(--timeline-height)',
            transform: panels.history ? 'translateY(0)' : 'translateY(100%)',
            transition: 'transform 300ms cubic-bezier(0.0, 0, 0.2, 1)',
            position: panels.history ? 'relative' : 'absolute',
            bottom: 0,
            left: 0,
            right: 0
          }}
        >
          <div className="p-6">
            <p className="text-sm text-muted">Version history will appear here</p>
          </div>
        </div>
      </main>

      {/* Conversation Sidebar - Dimension 2: Slide animation */}
      <aside
        className="studio-sidebar flex flex-col"
        style={{
          width: 'var(--sidebar-width)',
          transform: panels.conversation ? 'translateX(0)' : 'translateX(100%)',
          position: panels.conversation ? 'relative' : 'fixed',
          right: 0,
          height: '100%'
        }}
      >
          {/* Sidebar Header */}
          <div style={{ padding: '20px 24px', borderBottom: '1px solid rgba(218,221,216,0.4)' }}>
            <h3 className="font-heading" style={{ fontSize: '16px', fontWeight: 600, marginBottom: '6px' }}>
              Design Partner
            </h3>
            <p style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
              Let&rsquo;s discover what you&rsquo;re creating
            </p>
          </div>

          {/* Conversation Area */}
          <div className="flex-1 overflow-y-auto" style={{ padding: '24px' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {/* AI Welcome Message */}
              <div
                className="studio-panel rounded-lg"
                style={{
                  padding: '16px',
                  background: 'rgba(138, 141, 208, 0.08)',
                  borderColor: 'rgba(138, 141, 208, 0.2)'
                }}
              >
                <p style={{ fontSize: '14px', lineHeight: '1.6', color: 'var(--text)' }}>
                  What would you like to create today? Tell me about your project, and I&rsquo;ll guide
                  you through a thoughtful discovery process.
                </p>
              </div>

              {/* Suggested Questions */}
              <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
                <p style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                  Suggested questions
                </p>
                {[
                  "What's the purpose of your project?",
                  "Who is your audience?",
                  "Tell me about your content",
                ].map((question, i) => (
                  <button
                    key={i}
                    className="studio-button studio-button-secondary"
                    style={{ width: '100%', justifyContent: 'flex-start', textAlign: 'left' }}
                  >
                    {question}
                  </button>
                ))}
              </div>
            </div>
          </div>

          {/* Input Area */}
          <div style={{ padding: '24px', borderTop: '1px solid rgba(218,221,216,0.4)' }}>
            <input
              type="text"
              placeholder="Describe what you're creating..."
              className="studio-input"
            />
          </div>
        </aside>
    </div>
  )
}
