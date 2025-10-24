'use client'

import { useState } from 'react'
import { CopyIcon, CheckIcon } from '@/components/icons/Icon'
import type { Message } from '@/state/store'

interface ChatMessageProps {
  message: Message
  isGrouped?: boolean
  accentColor?: string
}

/**
 * Chat Message - Individual message with actions
 * Follows AI Chat UX Standards from PROACTIVE-DESIGN-PROTOCOL.md
 */
export function ChatMessage({ message, isGrouped = false, accentColor = 'var(--accent)' }: ChatMessageProps) {
  const [isCopied, setIsCopied] = useState(false)
  const isUser = message.role === 'user'

  const handleCopy = async () => {
    await navigator.clipboard.writeText(message.content)
    setIsCopied(true)
    setTimeout(() => setIsCopied(false), 2000)
  }

  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: isGrouped ? 'var(--space-2)' : 'var(--space-4)',
        alignItems: isUser ? 'flex-end' : 'flex-start',
        animation: 'fadeIn 200ms ease-out',
      }}
    >
      {/* Role label - only show if not grouped */}
      {!isGrouped && (
        <span
          style={{
            fontSize: '11px',
            color: 'var(--text-muted)',
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            fontWeight: 600,
            opacity: 0.6,
          }}
        >
          {isUser ? 'You' : 'Studio'}
        </span>
      )}

      {/* Message bubble */}
      <div
        style={{
          position: 'relative',
          display: 'flex',
          flexDirection: 'column',
          gap: 'var(--space-2)',
        }}
      >
        <div
          style={{
            padding: 'var(--space-3) var(--space-4)',
            borderRadius: 'var(--radius-lg)',
            maxWidth: '480px',
            fontSize: '14px',
            lineHeight: '1.6',
            background: isUser ? 'var(--color-accent-subtle)' : 'var(--surface-muted)',
            color: 'var(--text-primary)',
            wordBreak: 'break-word',
            whiteSpace: 'pre-wrap',
          }}
        >
          {message.content}
        </div>

        {/* Message actions - show on hover for AI messages */}
        {!isUser && (
          <div
            className="message-actions"
            style={{
              position: 'absolute',
              right: 'var(--space-2)',
              bottom: '-24px',
              display: 'flex',
              gap: 'var(--space-1)',
              opacity: 0,
              transition: 'opacity 200ms',
            }}
          >
            <button
              onClick={handleCopy}
              className="studio-button studio-button-ghost studio-button-sm"
              style={{
                padding: 'var(--space-1-5)',
                width: '28px',
                height: '28px',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
              }}
              aria-label="Copy message"
            >
              {isCopied ? <CheckIcon size={14} /> : <CopyIcon size={14} />}
            </button>
          </div>
        )}
      </div>

      <style jsx>{`
        .message-actions {
          opacity: 0;
        }
        div:hover > .message-actions {
          opacity: 1;
        }
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(4px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
      `}</style>
    </div>
  )
}
