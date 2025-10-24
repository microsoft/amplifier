'use client'

import { useEffect, useState } from 'react'
import { supabase } from '@/lib/supabase'

export default function TestDbPage() {
  const [status, setStatus] = useState<'checking' | 'success' | 'error'>('checking')
  const [message, setMessage] = useState('')
  const [projectCount, setProjectCount] = useState(0)

  useEffect(() => {
    checkDatabase()
  }, [])

  async function checkDatabase() {
    try {
      // Try to query projects table
      const { data, error } = await supabase
        .from('projects')
        .select('*')
        .limit(5)

      if (error) {
        setStatus('error')
        setMessage(`Database tables NOT found: ${error.message}`)
      } else {
        setStatus('success')
        setProjectCount(data.length)
        setMessage(`Database tables exist! Found ${data.length} projects.`)
      }
    } catch (err) {
      setStatus('error')
      setMessage(`Error: ${err}`)
    }
  }

  return (
    <div style={{
      padding: '40px',
      fontFamily: 'monospace',
      background: 'var(--background)',
      minHeight: '100vh',
      color: 'var(--text)'
    }}>
      <h1 style={{ marginBottom: '20px' }}>Database Connection Test</h1>

      <div style={{
        padding: '20px',
        borderRadius: '8px',
        background: status === 'success' ? '#10b981' : status === 'error' ? '#ef4444' : '#6b7280',
        color: 'white',
        marginBottom: '20px'
      }}>
        <strong>Status:</strong> {status.toUpperCase()}
        <br />
        <strong>Message:</strong> {message}
      </div>

      {status === 'error' && (
        <div style={{
          padding: '20px',
          background: 'rgba(239, 68, 68, 0.1)',
          borderRadius: '8px',
          border: '1px solid #ef4444'
        }}>
          <h2 style={{ marginBottom: '10px' }}>Fix Required:</h2>
          <ol style={{ paddingLeft: '20px' }}>
            <li>Go to Supabase Dashboard</li>
            <li>Open SQL Editor</li>
            <li>Run the migration file: <code>supabase/migrations/001_initial_schema.sql</code></li>
            <li>Refresh this page</li>
          </ol>
        </div>
      )}

      {status === 'success' && (
        <div style={{
          padding: '20px',
          background: 'rgba(16, 185, 129, 0.1)',
          borderRadius: '8px',
          border: '1px solid #10b981'
        }}>
          <h2 style={{ marginBottom: '10px' }}>✅ Database Ready!</h2>
          <p>You can now create and save projects.</p>
          <p>Projects found: {projectCount}</p>
        </div>
      )}

      <div style={{ marginTop: '40px' }}>
        <button
          onClick={checkDatabase}
          style={{
            padding: '12px 24px',
            background: 'var(--primary)',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontSize: '16px'
          }}
        >
          Recheck Database
        </button>
      </div>
    </div>
  )
}
