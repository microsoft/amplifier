'use client'

import { useEffect } from 'react'
import { useStudioStore } from '@/state/store'

/**
 * Delete Confirmation Modal
 * Shows when deleting >3 items for safety
 */
export function DeleteConfirmModal() {
  const deleteConfirmation = useStudioStore((state) => state.deleteConfirmation)
  const hideDeleteConfirmation = useStudioStore((state) => state.hideDeleteConfirmation)
  const deleteArtifacts = useStudioStore((state) => state.deleteArtifacts)

  useEffect(() => {
    if (!deleteConfirmation.show) return

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Enter') {
        e.preventDefault()
        handleConfirm()
      } else if (e.key === 'Escape') {
        e.preventDefault()
        hideDeleteConfirmation()
      }
    }

    window.addEventListener('keydown', handleKeyDown)
    return () => window.removeEventListener('keydown', handleKeyDown)
  }, [deleteConfirmation.show, deleteConfirmation.ids, hideDeleteConfirmation])

  if (!deleteConfirmation.show) return null

  const handleConfirm = () => {
    deleteArtifacts(deleteConfirmation.ids)
  }

  const handleCancel = () => {
    hideDeleteConfirmation()
  }

  return (
    <>
      {/* Overlay */}
      <div
        onClick={handleCancel}
        style={{
          position: 'fixed',
          inset: 0,
          background: 'rgba(0, 0, 0, 0.4)',
          zIndex: 9998,
          animation: 'modal-overlay-appear 200ms cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      />

      {/* Modal */}
      <div
        style={{
          position: 'fixed',
          top: '50%',
          left: '50%',
          transform: 'translate(-50%, -50%)',
          background: 'white',
          padding: '24px',
          borderRadius: '12px',
          boxShadow: '0 8px 32px rgba(0, 0, 0, 0.2)',
          maxWidth: '400px',
          width: '90%',
          zIndex: 9999,
          animation: 'modal-appear 200ms cubic-bezier(0.4, 0, 0.2, 1)',
        }}
      >
        {/* Title */}
        <h3
          style={{
            fontSize: '18px',
            fontWeight: 600,
            marginBottom: '12px',
            color: 'var(--text-primary)',
          }}
        >
          Delete {deleteConfirmation.ids.length} items?
        </h3>

        {/* Message */}
        <p
          style={{
            fontSize: '14px',
            lineHeight: '1.5',
            color: 'var(--text-muted)',
            marginBottom: '24px',
          }}
        >
          This action cannot be undone. Are you sure you want to delete these items?
        </p>

        {/* Actions */}
        <div
          style={{
            display: 'flex',
            gap: '12px',
            justifyContent: 'flex-end',
          }}
        >
          <button
            onClick={handleCancel}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: '1px solid var(--border)',
              background: 'white',
              color: 'var(--text-primary)',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'background 150ms',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.background = 'var(--bg-secondary, #F5F5F5)')}
            onMouseLeave={(e) => (e.currentTarget.style.background = 'white')}
          >
            Cancel <span style={{ opacity: 0.5 }}>(Esc)</span>
          </button>

          <button
            onClick={handleConfirm}
            style={{
              padding: '8px 16px',
              borderRadius: '8px',
              border: 'none',
              background: 'var(--error, #E53E3E)',
              color: 'white',
              fontSize: '14px',
              fontWeight: 500,
              cursor: 'pointer',
              transition: 'opacity 150ms',
            }}
            onMouseEnter={(e) => (e.currentTarget.style.opacity = '0.9')}
            onMouseLeave={(e) => (e.currentTarget.style.opacity = '1')}
          >
            Delete <span style={{ opacity: 0.7 }}>(Enter)</span>
          </button>
        </div>
      </div>
    </>
  )
}