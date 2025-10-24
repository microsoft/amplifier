'use client'

import { useRef, useEffect } from 'react'
import { ChatMessage } from './ChatMessage'
import { ChatInput } from './ChatInput'
import { TypingIndicator } from './TypingIndicator'
import { ConversationIcon } from '@/components/icons/Icon'
import type { Message } from '@/state/store'

interface ChatPanelProps {
  messages: Message[]
  isThinking: boolean
  onSend: (message: string) => void
  accentColor?: string
  suggestedQuestions?: string[]
}

/**
 * Chat Panel - Docked chat interface for discovery workspace
 * Refined with AI Chat UX Standards from PROACTIVE-DESIGN-PROTOCOL.md
 */
export function ChatPanel({
  messages,
  isThinking,
  onSend,
  accentColor = 'var(--accent)',
  suggestedQuestions = [],
}: ChatPanelProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null)
  const messagesContainerRef = useRef<HTMLDivElement>(null)

  // Display messages with initial greeting
  const displayMessages =
    messages.length === 0
      ? [
          {
            id: 'initial',
            role: 'ai' as const,
            content: "What would you like to create? As we chat, I'll build a workspace for you.",
            timestamp: Date.now(),
          },
        ]
      : messages

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({
        behavior: 'smooth',
        block: 'end',
      })
    }
  }, [messages.length, isThinking])

  // Group messages by sender for cleaner UI
  const groupedMessages = displayMessages.reduce((groups: Array<{ role: 'user' | 'ai'; messages: Message[] }>, message) => {
    const lastGroup = groups[groups.length - 1]
    if (lastGroup && lastGroup.role === message.role) {
      lastGroup.messages.push(message)
    } else {
      groups.push({ role: message.role, messages: [message] })
    }
    return groups
  }, [])

  return (
    <div
      className="studio-panel"
      style={{
        display: 'flex',
        flexDirection: 'column',
        height: '100%',
        borderRadius: '0',
        boxShadow: 'none',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: 'var(--space-4) var(--space-5)',
          borderBottom: '1px solid var(--border)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--space-2-5)',
        }}
      >
        <ConversationIcon size={20} />
        <span
          className="font-heading"
          style={{ fontSize: '15px', fontWeight: 600, color: 'var(--text-primary)' }}
        >
          Chat with Studio
        </span>
      </div>

      {/* Messages */}
      <div
        ref={messagesContainerRef}
        style={{
          flex: 1,
          overflowY: 'auto',
          padding: 'var(--space-6) var(--space-5)',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-6)',
        }}
      >
        {groupedMessages.map((group, groupIndex) => (
          <div key={groupIndex} style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-2)' }}>
            {group.messages.map((message, messageIndex) => (
              <ChatMessage
                key={message.id}
                message={message}
                isGrouped={messageIndex > 0}
                accentColor={accentColor}
              />
            ))}
          </div>
        ))}

        {isThinking && <TypingIndicator accentColor={accentColor} />}

        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <div
        style={{
          padding: 'var(--space-4) var(--space-5)',
          borderTop: '1px solid var(--border)',
        }}
      >
        <ChatInput
          onSend={onSend}
          disabled={isThinking}
          placeholder={messages.length === 0 ? "What would you like to create?" : "Continue the conversation..."}
          accentColor={accentColor}
          suggestedQuestions={suggestedQuestions}
        />
      </div>
    </div>
  )
}
