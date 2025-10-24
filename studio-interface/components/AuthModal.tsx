'use client'

import { useState, useEffect } from 'react'
import { useAuth } from '@/lib/hooks/useAuth'

interface AuthModalProps {
  isOpen: boolean
  onClose: () => void
}

export function AuthModal({ isOpen, onClose }: AuthModalProps) {
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [isRevealed, setIsRevealed] = useState(false)
  const { signInWithMagicLink } = useAuth()

  // Progressive reveal on mount
  useEffect(() => {
    if (isOpen) {
      requestAnimationFrame(() => {
        setIsRevealed(true)
      })
    } else {
      setIsRevealed(false)
      // Reset form when closed
      setEmail('')
      setError(null)
      setSuccess(null)
    }
  }, [isOpen])

  const handleMagicLink = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setSuccess(null)
    setIsSubmitting(true)

    try {
      const { error } = await signInWithMagicLink(email)

      if (error) {
        setError(error.message)
      } else {
        setSuccess('Check your email for the magic link!')
      }
      setIsSubmitting(false)
    } catch {
      setError('An unexpected error occurred')
      setIsSubmitting(false)
    }
  }

  if (!isOpen) return null

  return (
    <>
      {/* Backdrop */}
      <div
        className="fixed inset-0 z-50"
        style={{
          background: 'var(--modal-backdrop-bg)',
          backdropFilter: 'var(--modal-backdrop-blur)',
          WebkitBackdropFilter: 'var(--modal-backdrop-blur)',
          opacity: isRevealed ? 1 : 0,
          transition: 'opacity 200ms cubic-bezier(0.4, 0, 0.2, 1)',
        }}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        className="fixed inset-0 z-50 flex items-center justify-center"
        style={{ pointerEvents: 'none' }}
      >
        <div
          style={{
            pointerEvents: 'auto',
            width: '100%',
            maxWidth: '400px',
            padding: 'var(--space-8)',
            background: 'var(--bg-primary)',
            border: '1px solid var(--border)',
            borderRadius: '12px',
            boxShadow: 'var(--shadow-panel)',
            opacity: isRevealed ? 1 : 0,
            transform: isRevealed ? 'scale(1)' : 'scale(0.95)',
            transition: 'opacity 200ms cubic-bezier(0.4, 0, 0.2, 1), transform 200ms cubic-bezier(0.4, 0, 0.2, 1)',
          }}
        >
          <h2
            className="font-heading"
            style={{
              fontSize: '24px',
              fontWeight: 600,
              marginBottom: 'var(--space-2)',
              letterSpacing: '-0.01em',
            }}
          >
            Welcome to Studio
          </h2>

          <p
            style={{
              fontSize: '14px',
              color: 'var(--text-muted)',
              marginBottom: 'var(--space-8)',
            }}
          >
            Sign in to save and access your projects
          </p>

          {/* Magic Link Form */}
          <form onSubmit={handleMagicLink}>
            <div style={{ marginBottom: 'var(--space-6)' }}>
              <label
                htmlFor="email"
                style={{
                  display: 'block',
                  fontSize: '14px',
                  fontWeight: 500,
                  marginBottom: 'var(--space-2)',
                }}
              >
                Email address
              </label>
              <input
                id="email"
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
                placeholder="you@example.com"
                style={{
                  width: '100%',
                  padding: 'var(--space-3)',
                  fontSize: '14px',
                  border: '1px solid var(--border)',
                  borderRadius: '8px',
                  background: 'var(--bg-primary)',
                  transition: 'border-color 150ms cubic-bezier(0.4, 0, 0.2, 1)',
                }}
                onFocus={(e) => {
                  e.currentTarget.style.borderColor = 'var(--primary)'
                }}
                onBlur={(e) => {
                  e.currentTarget.style.borderColor = 'var(--border)'
                }}
              />
            </div>

            {error && (
              <div
                style={{
                  padding: 'var(--space-3)',
                  marginBottom: 'var(--space-4)',
                  fontSize: '14px',
                  color: 'var(--color-error)',
                  background: 'rgba(255, 0, 0, 0.05)',
                  border: '1px solid var(--color-error)',
                  borderRadius: '8px',
                }}
              >
                {error}
              </div>
            )}

            {success && (
              <div
                style={{
                  padding: 'var(--space-3)',
                  marginBottom: 'var(--space-4)',
                  fontSize: '14px',
                  color: 'var(--color-success)',
                  background: 'rgba(0, 255, 0, 0.05)',
                  border: '1px solid var(--color-success)',
                  borderRadius: '8px',
                }}
              >
                {success}
              </div>
            )}

            <button
              type="submit"
              className="studio-button studio-button-primary"
              disabled={isSubmitting}
              style={{
                width: '100%',
                opacity: isSubmitting ? 0.5 : 1,
              }}
            >
              {isSubmitting ? 'Sending...' : 'Send magic link'}
            </button>
          </form>

          <p
            style={{
              fontSize: '13px',
              color: 'var(--text-muted)',
              marginTop: 'var(--space-4)',
              textAlign: 'center',
            }}
          >
            We&rsquo;ll email you a link to sign in instantly
          </p>
        </div>
      </div>
    </>
  )
}
