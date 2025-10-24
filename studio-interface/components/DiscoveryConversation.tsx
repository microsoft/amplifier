'use client'

import { useState } from 'react'
import { useStudioStore } from '@/state/store'
import { useProject } from '@/lib/hooks/useProject'

/**
 * Discovery Conversation - AI asks thoughtful questions
 * Builds understanding before generating anything
 */
export function DiscoveryConversation() {
  const { messages, addMessage, setPhase } = useStudioStore()
  const { saveMessage, updateProjectStatus } = useProject()
  const [input, setInput] = useState('')
  const [isThinking, setIsThinking] = useState(false)

  // Initial AI greeting if no messages
  const displayMessages = messages.length === 0
    ? [{
        id: 'initial',
        role: 'ai' as const,
        content: 'What would you like to create today? Tell me about your project, and I\'ll guide you through a thoughtful discovery process.',
        timestamp: Date.now()
      }]
    : messages

  const handleSend = async () => {
    if (!input.trim()) return

    // Add user message
    const userContent = input
    addMessage({ role: 'user', content: userContent })
    setInput('')
    setIsThinking(true)

    try {
      // Save user message to database
      await saveMessage('user', userContent)

      // Call Claude API
      const response = await fetch('/api/chat', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          messages: [...messages, { role: 'user', content: userContent }],
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

      setIsThinking(false)

      // Transition to express phase after enough discovery (8+ messages means 4+ exchanges)
      if (messages.length >= 8) {
        // Update project status
        await updateProjectStatus('expression')

        setTimeout(() => {
          setPhase('express')
        }, 2000)
      }
    } catch (error) {
      console.error('Chat error:', error)
      addMessage({
        role: 'ai',
        content: 'I apologize, I had trouble responding. Could you try again?',
      })
      setIsThinking(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex h-screen w-screen flex-col studio-canvas">
      {/* Minimal Toolbar */}
      <div className="studio-toolbar flex items-center justify-between" style={{ height: 'var(--toolbar-height)' }}>
        <div className="flex items-center gap-3 px-6">
          <h1 className="font-heading" style={{ fontSize: '20px', fontWeight: 600, letterSpacing: '-0.01em' }}>
            Studio
          </h1>
          <span style={{ fontSize: '13px', color: 'var(--text-muted)' }}>
            Discovery
          </span>
        </div>
      </div>

      {/* Conversation Area */}
      <div className="flex-1 overflow-y-auto" style={{ padding: '48px', maxWidth: '800px', margin: '0 auto', width: '100%' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '32px' }}>
          {displayMessages.map((message) => (
            <div
              key={message.id}
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: '8px',
                alignItems: message.role === 'user' ? 'flex-end' : 'flex-start'
              }}
            >
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                {message.role === 'ai' ? 'Studio' : 'You'}
              </span>
              <div
                className="studio-panel"
                style={{
                  padding: '20px 24px',
                  borderRadius: '12px',
                  maxWidth: '85%',
                  background: message.role === 'ai'
                    ? 'rgba(138, 141, 208, 0.08)'
                    : 'rgba(28, 28, 28, 0.04)',
                  borderColor: message.role === 'ai'
                    ? 'rgba(138, 141, 208, 0.2)'
                    : 'rgba(28, 28, 28, 0.1)'
                }}
              >
                <p style={{ fontSize: '16px', lineHeight: '1.6', margin: 0 }}>
                  {message.content}
                </p>
              </div>
            </div>
          ))}

          {isThinking && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', alignItems: 'flex-start' }}>
              <span style={{ fontSize: '11px', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.05em', fontWeight: 500 }}>
                Studio
              </span>
              <div
                className="studio-panel ai-thinking"
                style={{
                  padding: '20px 24px',
                  borderRadius: '12px',
                  background: 'rgba(138, 141, 208, 0.08)',
                  borderColor: 'rgba(138, 141, 208, 0.2)'
                }}
              >
                <p style={{ fontSize: '16px', lineHeight: '1.6', margin: 0, color: 'var(--text-muted)' }}>
                  Thinking...
                </p>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Input Area */}
      <div
        className="studio-panel border-t"
        style={{
          padding: '24px 48px',
          maxWidth: '800px',
          margin: '0 auto',
          width: '100%'
        }}
      >
        <div style={{ display: 'flex', gap: '12px', alignItems: 'flex-end' }}>
          <textarea
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Tell me about your project..."
            disabled={isThinking}
            style={{
              flex: 1,
              minHeight: '44px',
              maxHeight: '200px',
              padding: '12px 16px',
              fontFamily: 'var(--font-geist-sans), sans-serif',
              fontSize: '15px',
              lineHeight: '1.5',
              background: 'var(--background)',
              color: 'var(--text)',
              border: '1px solid rgba(218, 221, 216, 0.6)',
              borderRadius: '8px',
              outline: 'none',
              resize: 'vertical',
              transition: 'border-color 200ms'
            }}
            onFocus={(e) => e.target.style.borderColor = 'var(--text)'}
            onBlur={(e) => e.target.style.borderColor = 'rgba(218, 221, 216, 0.6)'}
          />
          <button
            className="studio-button studio-button-primary"
            onClick={handleSend}
            disabled={!input.trim() || isThinking}
            style={{
              height: '44px',
              opacity: (!input.trim() || isThinking) ? 0.5 : 1,
              cursor: (!input.trim() || isThinking) ? 'not-allowed' : 'pointer'
            }}
          >
            Send
          </button>
        </div>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '12px', opacity: 0.6 }}>
          Press Enter to send, Shift+Enter for new line
        </p>
      </div>
    </div>
  )
}
