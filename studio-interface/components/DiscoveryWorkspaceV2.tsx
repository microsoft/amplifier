'use client'

import { useState, useEffect } from 'react'
import { useStudioStore } from '@/state/store'
import { useProject } from '@/lib/hooks/useProject'
import { useProjectSync } from '@/hooks/useProjectSync'
import { extractEntities } from '@/lib/entityExtraction'
import { organizeArtifacts, type LayoutInstructions } from '@/lib/canvasLayout'
import { DiscoveryCanvas } from './DiscoveryCanvas'
import { ChatPanel } from './chat/ChatPanel'
import { PhaseNavigator } from './PhaseNavigator'
import { SettingsModal } from './SettingsModal'
import { ProjectSwitcher } from './ProjectSwitcher'
import { SettingsIcon, MessageCircleIcon } from './icons/Icon'

/**
 * Discovery Workspace V2 - Split layout with canvas and docked chat
 * Chat starts docked on the right, canvas expands as artifacts are added
 */
export function DiscoveryWorkspaceV2() {
  const { messages, addMessage, addArtifact, setPhase, canvasArtifacts, updateArtifact } = useStudioStore()
  const { saveMessage, updateProjectStatus } = useProject()
  const [isThinking, setIsThinking] = useState(false)
  const [showSettings, setShowSettings] = useState(false)
  const [showChat, setShowChat] = useState(true)
  const [isRevealed, setIsRevealed] = useState(false)

  // Auto-save project state when artifacts/messages change
  useProjectSync()

  // Progressive reveal on mount
  useEffect(() => {
    // Trigger reveal after component mounts
    requestAnimationFrame(() => {
      setIsRevealed(true)
    })
  }, [])

  const handleSend = async (userContent: string) => {
    const messageId = crypto.randomUUID()

    // Extract entities and create artifacts BEFORE adding message
    const artifacts = extractEntities(userContent)
    artifacts.forEach((artifactData) => {
      addArtifact({
        ...artifactData,
        sourceMessageId: messageId,
      })
    })

    // Add user message
    addMessage({ role: 'user', content: userContent })
    setIsThinking(true)

    try {
      // Save user message to database
      await saveMessage('user', userContent)

      // Call Claude API with canvas context
      console.log('🔍 Sending to chat API:')
      console.log('- Canvas artifacts count:', canvasArtifacts.length)
      console.log('- Artifacts:', canvasArtifacts)

      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, { role: 'user', content: userContent }],
          canvasArtifacts: canvasArtifacts, // Send full canvas context
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to get response')
      }

      const data = await response.json()

      // Add AI message to state
      addMessage({
        role: 'ai',
        content: data.message,
      })

      // Save AI message to database
      await saveMessage('ai', data.message)

      // Handle layout instructions if provided
      if (data.layoutInstructions) {
        console.log('📐 Organizing canvas with instructions:', data.layoutInstructions)
        const updates = organizeArtifacts(canvasArtifacts, data.layoutInstructions as LayoutInstructions)

        // Apply position updates to artifacts
        updates.forEach(({ id, position }) => {
          const artifact = canvasArtifacts.find(a => a.id === id)
          if (artifact) {
            updateArtifact(id, { position })
          }
        })
      }

      setIsThinking(false)
    } catch (error) {
      console.error('Chat error:', error)
      addMessage({
        role: 'ai',
        content: 'I apologize, I had trouble responding. Could you try again?',
      })
      setIsThinking(false)
    }
  }

  return (
    <div className="flex h-screen w-screen flex-col studio-canvas">
      {/* Toolbar - Frameless with gradient mask */}
      <div
        style={{
          position: 'absolute',
          top: 0,
          left: 0,
          right: 0,
          height: 'var(--toolbar-height)',
          zIndex: 100,
          pointerEvents: 'none',
        }}
      >
        {/* Gradient mask for content visibility */}
        <div
          style={{
            position: 'absolute',
            inset: 0,
            background: 'linear-gradient(to bottom, var(--background) 0%, var(--background) 50%, transparent 100%)',
            pointerEvents: 'none',
          }}
        />

        {/* Toolbar content */}
        <div
          style={{
            position: 'relative',
            height: '100%',
            opacity: isRevealed ? 1 : 0,
            transform: isRevealed ? 'translateY(0)' : 'translateY(-10px)',
            transition: 'opacity 200ms cubic-bezier(0.4, 0, 0.2, 1), transform 200ms cubic-bezier(0.4, 0, 0.2, 1)',
            transitionDelay: '0ms',
            pointerEvents: 'auto',
          }}
        >
          {/* Left: Project Switcher */}
          <div
            className="flex items-center gap-4 px-6"
            style={{
              position: 'absolute',
              left: 0,
              top: '50%',
              transform: 'translateY(-50%)',
            }}
          >
            <ProjectSwitcher onNavigateHome={() => setPhase('empty')} />
          </div>

          {/* Center: Phase Navigator - Absolute centered */}
          <div
            style={{
              position: 'absolute',
              left: '50%',
              top: '50%',
              transform: 'translate(-50%, -50%)',
            }}
          >
            <PhaseNavigator />
          </div>

          {/* Right: Chat toggle + Settings buttons */}
          <div
            className="flex items-center gap-2 px-6"
            style={{
              position: 'absolute',
              right: 0,
              top: '50%',
              transform: 'translateY(-50%)',
            }}
          >
            <button
              className="studio-button studio-button-icon"
              onClick={() => setShowChat(!showChat)}
              aria-label="Toggle chat"
              style={{
                background: showChat ? 'var(--bg-primary)' : 'transparent',
                border: showChat ? '1px solid var(--border)' : 'none',
              }}
            >
              <MessageCircleIcon size={18} />
            </button>
            <button
              className="studio-button studio-button-icon"
              onClick={() => setShowSettings(!showSettings)}
              aria-label="Settings"
            >
              <SettingsIcon size={18} />
            </button>
          </div>
        </div>
      </div>

      {/* Main Content - Canvas with floating chat */}
      <div
        className="flex-1 relative overflow-hidden"
        style={{
          opacity: isRevealed ? 1 : 0,
          transition: 'opacity 200ms cubic-bezier(0.4, 0, 0.2, 1)',
          transitionDelay: '100ms',
        }}
      >
        {/* Canvas - Full width */}
        <DiscoveryCanvas />

        {/* Chat Panel - Floating over canvas on right side */}
        {showChat && (
          <div
            style={{
              position: 'absolute',
              top: 0,
              right: 0,
              bottom: 0,
              width: '440px',
              padding: '24px',
              paddingTop: 'calc(var(--toolbar-height) + 24px)', // Clear toolbar space
              paddingBottom: '24px',
              display: 'flex',
              flexDirection: 'column',
              pointerEvents: 'none', // Let clicks through to canvas
              opacity: isRevealed ? 1 : 0,
              transform: isRevealed && showChat ? 'translateX(0) scale(1)' : 'translateX(40px) scale(0.96)',
              transition: 'opacity 400ms cubic-bezier(0.4, 0, 0.2, 1), transform 500ms cubic-bezier(0.34, 1.56, 0.64, 1)',
              transitionDelay: '100ms',
            }}
          >
            <div
              style={{
                background: 'var(--bg-primary)',
                border: '1px solid var(--border)',
                borderRadius: '16px',
                boxShadow: '0 8px 24px rgba(0, 0, 0, 0.08), 0 2px 6px rgba(0, 0, 0, 0.04)',
                overflow: 'hidden',
                display: 'flex',
                flexDirection: 'column',
                height: '100%',
                pointerEvents: 'auto', // Re-enable clicks for chat panel
              }}
            >
              <ChatPanel
                messages={messages}
                isThinking={isThinking}
                onSend={handleSend}
                accentColor="#8A8DD0"
              />
            </div>
          </div>
        )}
      </div>

      {/* Settings Modal */}
      <SettingsModal isOpen={showSettings} onClose={() => setShowSettings(false)} />
    </div>
  )
}
