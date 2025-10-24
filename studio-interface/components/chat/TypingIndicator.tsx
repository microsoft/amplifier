'use client'

interface TypingIndicatorProps {
  accentColor?: string
}

/**
 * Typing Indicator - Animated dots for AI thinking state
 * Follows AI Chat UX Standards from PROACTIVE-DESIGN-PROTOCOL.md
 */
export function TypingIndicator({ accentColor = 'var(--accent)' }: TypingIndicatorProps) {
  return (
    <div
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: 'var(--space-2)',
        alignItems: 'flex-start',
      }}
    >
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
        Studio
      </span>

      <div
        style={{
          padding: 'var(--space-3) var(--space-4)',
          borderRadius: 'var(--radius-lg)',
          background: 'var(--surface-muted)',
          display: 'flex',
          gap: 'var(--space-1-5)',
          alignItems: 'center',
        }}
      >
        <div
          className="dot"
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: accentColor,
            opacity: 0.6,
            animation: 'bounce 1.4s infinite ease-in-out',
            animationDelay: '0s',
          }}
        />
        <div
          className="dot"
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: accentColor,
            opacity: 0.6,
            animation: 'bounce 1.4s infinite ease-in-out',
            animationDelay: '0.2s',
          }}
        />
        <div
          className="dot"
          style={{
            width: '8px',
            height: '8px',
            borderRadius: '50%',
            backgroundColor: accentColor,
            opacity: 0.6,
            animation: 'bounce 1.4s infinite ease-in-out',
            animationDelay: '0.4s',
          }}
        />

        <style jsx>{`
          @keyframes bounce {
            0%,
            60%,
            100% {
              transform: translateY(0);
              opacity: 0.6;
            }
            30% {
              transform: translateY(-6px);
              opacity: 1;
            }
          }
        `}</style>
      </div>
    </div>
  )
}
