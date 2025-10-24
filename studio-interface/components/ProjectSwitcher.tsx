'use client'

import { useState, useRef, useEffect } from 'react'
import { useStudioStore } from '@/state/store'
import { ChevronDownIcon, ProjectIcon, PencilIcon, CheckIcon, HomeIcon } from './icons/Icon'

/**
 * Project Switcher Component
 *
 * Purpose: Allow users to see current project, rename it, and navigate to projects home
 * Location: Toolbar (left side, replaces hardcoded "Studio | Untitled Project")
 *
 * Features:
 * - Shows current project name
 * - Click to open dropdown menu
 * - Rename project inline
 * - Navigate to projects home
 * - Keyboard accessible
 */

interface ProjectSwitcherProps {
  onNavigateHome: () => void
}

export function ProjectSwitcher({ onNavigateHome }: ProjectSwitcherProps) {
  const { project, setProject } = useStudioStore()
  const [isOpen, setIsOpen] = useState(false)
  const [isEditing, setIsEditing] = useState(false)
  const [editName, setEditName] = useState(project?.name || '')
  const dropdownRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLInputElement>(null)

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(event: MouseEvent) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target as Node)) {
        setIsOpen(false)
        setIsEditing(false)
      }
    }

    if (isOpen) {
      document.addEventListener('mousedown', handleClickOutside)
      return () => document.removeEventListener('mousedown', handleClickOutside)
    }
  }, [isOpen])

  // Focus input when editing starts
  useEffect(() => {
    if (isEditing && inputRef.current) {
      inputRef.current.focus()
      inputRef.current.select()
    }
  }, [isEditing])

  const handleRename = () => {
    if (editName.trim() && project) {
      setProject({
        ...project,
        name: editName.trim(),
      })
      setIsEditing(false)
      setIsOpen(false)
    }
  }

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter') {
      handleRename()
    } else if (e.key === 'Escape') {
      setEditName(project?.name || '')
      setIsEditing(false)
    }
  }

  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center', gap: 'var(--space-3)' }} ref={dropdownRef}>
      {/* Studio Brand */}
      <h1
        className="font-heading"
        style={{
          fontSize: '20px',
          fontWeight: 600,
          letterSpacing: '-0.01em',
          margin: 0,
          cursor: 'pointer',
          transition: 'transform 150ms cubic-bezier(0.4, 0, 0.2, 1), opacity 150ms cubic-bezier(0.4, 0, 0.2, 1)',
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.transform = 'scale(1.02)'
          e.currentTarget.style.opacity = '0.9'
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.transform = 'scale(1)'
          e.currentTarget.style.opacity = '1'
        }}
        onClick={() => onNavigateHome()}
      >
        Studio
      </h1>

      {/* Project Switcher (only if project exists) */}
      {project && (
        <>
          <span style={{ color: 'var(--text-muted)', fontSize: '20px', fontWeight: 300 }}>|</span>

          <button
            onClick={() => setIsOpen(!isOpen)}
            className="studio-button"
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              padding: 'var(--space-2) var(--space-3)',
              background: isOpen ? 'var(--bg-hover)' : 'transparent',
              border: 'none',
              borderRadius: 'var(--radius-sm)',
              cursor: 'pointer',
              transition: 'background 150ms ease',
            }}
            aria-expanded={isOpen}
            aria-haspopup="true"
          >
            <ProjectIcon size={18} />
            <span
              style={{
                fontSize: '15px',
                fontWeight: 500,
                color: 'var(--text-primary)',
                maxWidth: '200px',
                overflow: 'hidden',
                textOverflow: 'ellipsis',
                whiteSpace: 'nowrap',
              }}
            >
              {project.name}
            </span>
            <span
              style={{
                display: 'inline-flex',
                transform: isOpen ? 'rotate(180deg)' : 'rotate(0deg)',
                transition: 'transform 150ms ease',
              }}
            >
              <ChevronDownIcon size={16} />
            </span>
          </button>
        </>
      )}

      {/* Dropdown Menu */}
      {isOpen && (
        <div
          style={{
            position: 'absolute',
            top: 'calc(100% + var(--space-2))',
            left: 0,
            minWidth: '280px',
            background: 'var(--bg-secondary)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--radius-md)',
            boxShadow: 'var(--shadow-elevated)',
            zIndex: 1000,
            overflow: 'hidden',
          }}
        >
          {/* Current Project Section */}
          <div
            style={{
              padding: 'var(--space-3)',
              borderBottom: '1px solid var(--border)',
            }}
          >
            <div
              style={{
                fontSize: '11px',
                fontWeight: 600,
                textTransform: 'uppercase',
                letterSpacing: '0.05em',
                color: 'var(--text-muted)',
                marginBottom: 'var(--space-2)',
              }}
            >
              Current Project
            </div>

            {isEditing ? (
              /* Edit Mode */
              <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                <input
                  ref={inputRef}
                  type="text"
                  value={editName}
                  onChange={(e) => setEditName(e.target.value)}
                  onKeyDown={handleKeyDown}
                  className="studio-input"
                  style={{
                    flex: 1,
                    padding: 'var(--space-2)',
                    fontSize: '14px',
                  }}
                  onFocus={(e) => e.target.style.borderColor = 'var(--primary)'}
                  onBlur={(e) => e.target.style.borderColor = 'var(--border)'}
                />
                <button
                  onClick={handleRename}
                  className="studio-button-icon"
                  style={{
                    width: '32px',
                    height: '32px',
                    padding: 0,
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    background: 'var(--primary)',
                    border: 'none',
                    borderRadius: 'var(--radius-sm)',
                    cursor: 'pointer',
                    color: 'var(--bg-primary)',
                  }}
                  aria-label="Save"
                >
                  <CheckIcon size={16} />
                </button>
              </div>
            ) : (
              /* Display Mode */
              <div style={{ display: 'flex', gap: 'var(--space-2)', alignItems: 'center' }}>
                <span
                  style={{
                    flex: 1,
                    fontSize: '14px',
                    fontWeight: 500,
                    color: 'var(--text-primary)',
                  }}
                >
                  {project?.name || 'Untitled Project'}
                </span>
                <button
                  onClick={() => {
                    setEditName(project?.name || '')
                    setIsEditing(true)
                  }}
                  className="studio-button-icon"
                  style={{
                    width: '32px',
                    height: '32px',
                  }}
                  aria-label="Rename project"
                >
                  <PencilIcon size={14} />
                </button>
              </div>
            )}
          </div>

          {/* Actions Section */}
          <div style={{ padding: 'var(--space-2)' }}>
            <button
              onClick={() => {
                setIsOpen(false)
                onNavigateHome()
              }}
              style={{
                width: '100%',
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--space-2)',
                padding: 'var(--space-2) var(--space-3)',
                background: 'transparent',
                border: 'none',
                borderRadius: 'var(--radius-sm)',
                cursor: 'pointer',
                fontSize: '14px',
                color: 'var(--text-primary)',
                transition: 'background 150ms ease',
                textAlign: 'left',
              }}
              onMouseEnter={(e) => e.currentTarget.style.background = 'var(--bg-hover)'}
              onMouseLeave={(e) => e.currentTarget.style.background = 'transparent'}
            >
              <HomeIcon size={16} />
              All Projects
            </button>
          </div>
        </div>
      )}
    </div>
  )
}
