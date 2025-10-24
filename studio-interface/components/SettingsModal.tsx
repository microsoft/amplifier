'use client'

import { useState, useEffect } from 'react'
import { createPortal } from 'react-dom'
import { CloseIcon } from './icons/Icon'
import { useStudioStore } from '@/state/store'

/**
 * Settings Modal
 * Sidebar layout with sections (like ChatGPT settings)
 * Only includes working, functional settings
 */

type SettingsSection = 'general' | 'account'

interface SettingsModalProps {
  isOpen: boolean
  onClose: () => void
}

export function SettingsModal({ isOpen, onClose }: SettingsModalProps) {
  const [activeSection, setActiveSection] = useState<SettingsSection>('general')
  const [mounted, setMounted] = useState(false)

  useEffect(() => {
    setMounted(true)
  }, [])

  if (!isOpen || !mounted) return null

  const modalContent = (
    <>
      {/* Backdrop */}
      <div
        style={{
          position: 'fixed',
          inset: 0,
          background: 'var(--modal-backdrop-bg)',
          backdropFilter: 'var(--modal-backdrop-blur)',
          WebkitBackdropFilter: 'var(--modal-backdrop-blur)',
          zIndex: 9998,
          animation: 'fadeIn 200ms ease',
        }}
        onClick={onClose}
      />

      {/* Modal */}
      <div
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          width: '90%',
          maxWidth: '900px',
          height: '80vh',
          maxHeight: '600px',
          background: 'var(--bg-primary)',
          borderRadius: '12px',
          boxShadow: 'var(--shadow-modal)',
          display: 'flex',
          overflow: 'hidden',
          zIndex: 9999,
          animation: 'scaleIn 200ms ease',
        }}
      >
        {/* Sidebar */}
        <div
          style={{
            width: '200px',
            background: 'var(--bg-secondary)',
            borderRight: '1px solid var(--border-default)',
            padding: '16px',
            display: 'flex',
            flexDirection: 'column',
          }}
        >
          {/* Close button in sidebar */}
          <button
            onClick={onClose}
            style={{
              width: '32px',
              height: '32px',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              border: 'none',
              background: 'transparent',
              cursor: 'pointer',
              borderRadius: '6px',
              marginBottom: '16px',
              transition: 'background 150ms ease',
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = 'var(--bg-hover)'
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = 'transparent'
            }}
            aria-label="Close settings"
          >
            <CloseIcon size={18} />
          </button>

          {/* Navigation */}
          <nav style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
            <button
              onClick={() => setActiveSection('general')}
              style={{
                padding: '10px 12px',
                border: 'none',
                background: activeSection === 'general' ? 'var(--bg-primary)' : 'transparent',
                textAlign: 'left',
                cursor: 'pointer',
                borderRadius: '6px',
                fontSize: '14px',
                fontFamily: 'var(--font-geist-sans)',
                color: 'var(--text-primary)',
                transition: 'background 150ms ease',
              }}
              onMouseEnter={(e) => {
                if (activeSection !== 'general') {
                  e.currentTarget.style.background = 'var(--bg-hover)'
                }
              }}
              onMouseLeave={(e) => {
                if (activeSection !== 'general') {
                  e.currentTarget.style.background = 'transparent'
                }
              }}
            >
              General
            </button>

            <button
              onClick={() => setActiveSection('account')}
              style={{
                padding: '10px 12px',
                border: 'none',
                background: activeSection === 'account' ? 'var(--bg-primary)' : 'transparent',
                textAlign: 'left',
                cursor: 'pointer',
                borderRadius: '6px',
                fontSize: '14px',
                fontFamily: 'var(--font-geist-sans)',
                color: 'var(--text-primary)',
                transition: 'background 150ms ease',
              }}
              onMouseEnter={(e) => {
                if (activeSection !== 'account') {
                  e.currentTarget.style.background = 'var(--bg-hover)'
                }
              }}
              onMouseLeave={(e) => {
                if (activeSection !== 'account') {
                  e.currentTarget.style.background = 'transparent'
                }
              }}
            >
              Account
            </button>
          </nav>
        </div>

        {/* Content Area */}
        <div
          style={{
            flex: 1,
            padding: '32px',
            overflowY: 'auto',
          }}
        >
          {activeSection === 'general' && <GeneralSettings />}
          {activeSection === 'account' && <AccountSettings />}
        </div>
      </div>
    </>
  )

  return createPortal(modalContent, document.body)
}

function GeneralSettings() {
  const { theme, setTheme } = useStudioStore()

  return (
    <div>
      <h2
        style={{
          fontSize: '24px',
          fontWeight: 600,
          fontFamily: 'var(--font-heading)',
          marginBottom: '24px',
        }}
      >
        General
      </h2>

      {/* Theme */}
      <div style={{ marginBottom: '24px' }}>
        <label
          style={{
            display: 'block',
            fontSize: '14px',
            fontWeight: 500,
            marginBottom: '12px',
          }}
        >
          Theme
        </label>

        {/* Radio buttons for theme selection */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="radio"
              name="theme"
              value="auto"
              checked={theme === 'auto'}
              onChange={(e) => setTheme(e.target.value as 'auto' | 'light' | 'dark')}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ fontSize: '14px' }}>Auto (system preference)</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="radio"
              name="theme"
              value="light"
              checked={theme === 'light'}
              onChange={(e) => setTheme(e.target.value as 'auto' | 'light' | 'dark')}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ fontSize: '14px' }}>Light</span>
          </label>

          <label style={{ display: 'flex', alignItems: 'center', gap: '8px', cursor: 'pointer' }}>
            <input
              type="radio"
              name="theme"
              value="dark"
              checked={theme === 'dark'}
              onChange={(e) => setTheme(e.target.value as 'auto' | 'light' | 'dark')}
              style={{ cursor: 'pointer' }}
            />
            <span style={{ fontSize: '14px' }}>Dark</span>
          </label>
        </div>

        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '8px' }}>
          Choose how Studio looks to you
        </p>
      </div>

      {/* Language - Coming soon */}
      <div style={{ marginBottom: '24px' }}>
        <label
          style={{
            display: 'block',
            fontSize: '14px',
            fontWeight: 500,
            marginBottom: '8px',
            color: 'var(--text-muted)',
          }}
        >
          Language (Coming Soon)
        </label>
        <select
          disabled
          style={{
            width: '100%',
            padding: '8px 12px',
            border: '1px solid var(--border-default)',
            borderRadius: '6px',
            background: 'var(--bg-secondary)',
            fontSize: '14px',
            fontFamily: 'var(--font-geist-sans)',
            color: 'var(--text-muted)',
            cursor: 'not-allowed',
          }}
        >
          <option>English</option>
        </select>
        <p style={{ fontSize: '12px', color: 'var(--text-muted)', marginTop: '4px' }}>
          Multi-language support in development
        </p>
      </div>
    </div>
  )
}

function AccountSettings() {
  return (
    <div>
      <h2
        style={{
          fontSize: '24px',
          fontWeight: 600,
          fontFamily: 'var(--font-heading)',
          marginBottom: '24px',
        }}
      >
        Account
      </h2>

      <p style={{ fontSize: '14px', color: 'var(--text-muted)' }}>
        Account management coming soon.
      </p>
    </div>
  )
}
