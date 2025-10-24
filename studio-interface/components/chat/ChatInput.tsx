'use client'

import { useState, useRef, useEffect } from 'react'
import { ArrowRightIcon, MicIcon } from '@/components/icons/Icon'

const SCROLL_THRESHOLD = 10 // pixels from bottom to hide fade

interface ChatInputProps {
  onSend: (message: string) => void
  disabled?: boolean
  placeholder?: string
  accentColor?: string
  suggestedQuestions?: string[]
}

/**
 * Chat Input - Auto-growing textarea with send button
 * Follows AI Chat UX Standards from PROACTIVE-DESIGN-PROTOCOL.md
 */
export function ChatInput({
  onSend,
  disabled = false,
  placeholder = 'Type a message...',
  accentColor = 'var(--accent)',
  suggestedQuestions = [],
}: ChatInputProps) {
  const [input, setInput] = useState('')
  const [showFade, setShowFade] = useState(false)
  const textareaRef = useRef<HTMLTextAreaElement>(null)

  // Auto-grow textarea and check if content overflows
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      const scrollHeight = textareaRef.current.scrollHeight
      // Max 8 lines (roughly 160px)
      textareaRef.current.style.height = `${Math.min(scrollHeight, 160)}px`

      // Show fade indicator if content overflows and not scrolled to bottom
      const checkOverflow = () => {
        if (!textareaRef.current) return
        const { scrollHeight, clientHeight, scrollTop } = textareaRef.current
        const isOverflowing = scrollHeight > clientHeight
        const isAtBottom = scrollHeight - scrollTop - clientHeight < SCROLL_THRESHOLD
        setShowFade(isOverflowing && !isAtBottom)
      }

      checkOverflow()
      textareaRef.current.addEventListener('scroll', checkOverflow)

      return () => {
        textareaRef.current?.removeEventListener('scroll', checkOverflow)
      }
    }
  }, [input])

  const handleSend = () => {
    const trimmed = input.trim()
    if (trimmed && !disabled) {
      onSend(trimmed)
      setInput('')
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  const handleSuggestionClick = (question: string) => {
    onSend(question)
  }

  const canSend = input.trim().length > 0 && !disabled

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
      {/* Suggested questions - show if available and input is empty */}
      {suggestedQuestions.length > 0 && !input && (
        <div
          style={{
            display: 'flex',
            flexWrap: 'wrap',
            gap: 'var(--space-2)',
            animation: 'fadeIn 300ms ease-out 300ms both',
          }}
        >
          {suggestedQuestions.map((question, i) => (
            <button
              key={i}
              onClick={() => handleSuggestionClick(question)}
              disabled={disabled}
              className="studio-button studio-button-ghost studio-button-sm"
              style={{
                fontSize: '13px',
                padding: 'var(--space-1-5) var(--space-3)',
                borderRadius: 'var(--radius-md)',
                whiteSpace: 'nowrap',
                opacity: disabled ? 0.5 : 1,
              }}
            >
              {question}
            </button>
          ))}
        </div>
      )}

      {/* Input area - wrapper that looks like one input with buttons inside */}
      <div
        className="studio-input"
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          padding: '6px 6px 6px 16px',
          minHeight: '48px',
          position: 'relative',
        }}
      >
        {/* Textarea without border - blends into wrapper */}
        <textarea
          ref={textareaRef}
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          rows={1}
          style={{
            flex: 1,
            border: 'none',
            outline: 'none',
            background: 'transparent',
            fontSize: '14px',
            padding: '6px 0',
            lineHeight: '1.5',
            resize: 'none',
            fontFamily: 'inherit',
            color: 'inherit',
            minHeight: '21px', // Single line height
            maxHeight: '140px',
          }}
        />

        {/* Buttons */}
        <div
          style={{
            display: 'flex',
            gap: '4px',
            alignItems: 'center',
            flexShrink: 0,
          }}
        >
          {/* Mic button - icon only */}
          <button
            type="button"
            onClick={() => console.log('Mic clicked')} // TODO: Add mic functionality
            disabled={disabled}
            style={{
              width: '36px',
              height: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: 'none',
              background: 'transparent',
              cursor: disabled ? 'not-allowed' : 'pointer',
              opacity: disabled ? 0.4 : 0.6,
              transition: 'opacity 150ms',
              borderRadius: '6px',
            }}
            onMouseEnter={(e) => {
              if (!disabled) {
                e.currentTarget.style.opacity = '1'
                e.currentTarget.style.background = 'var(--color-hover)'
              }
            }}
            onMouseLeave={(e) => {
              if (!disabled) {
                e.currentTarget.style.opacity = '0.6'
                e.currentTarget.style.background = 'transparent'
              }
            }}
            aria-label="Voice input"
          >
            <MicIcon size={18} />
          </button>

          {/* Send button - primary */}
          <button
            onClick={handleSend}
            disabled={!canSend}
            className="studio-button studio-button-primary"
            style={{
              width: '36px',
              height: '36px',
              minWidth: '36px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              padding: '0',
              opacity: canSend ? 1 : 0.4,
              transform: canSend ? 'scale(1)' : 'scale(0.9)',
              transition: 'all 200ms cubic-bezier(0.34, 1.56, 0.64, 1)',
              pointerEvents: canSend ? 'auto' : 'none',
            }}
            onMouseEnter={(e) => {
              if (canSend) {
                e.currentTarget.style.transform = 'scale(1.1)'
              }
            }}
            onMouseLeave={(e) => {
              if (canSend) {
                e.currentTarget.style.transform = 'scale(1)'
              }
            }}
            aria-label="Send message"
          >
            <ArrowRightIcon size={18} />
          </button>
        </div>

        {/* Fade indicator for overflow */}
        {showFade && (
          <div
            style={{
              position: 'absolute',
              bottom: 6,
              left: 16,
              right: 96, // Clear button space
              height: '24px',
              background: 'linear-gradient(to bottom, transparent, var(--background))',
              pointerEvents: 'none',
              borderRadius: '0 0 6px 6px',
              opacity: 0.8,
              transition: 'opacity 200ms',
            }}
          />
        )}
      </div>

      <style jsx>{`
        @keyframes fadeIn {
          from {
            opacity: 0;
            transform: translateY(-4px);
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
