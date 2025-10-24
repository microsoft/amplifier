'use client'

export default function TestFABPage() {
  return (
    <div style={{
      width: '100vw',
      height: '100vh',
      background: 'var(--canvas-bg)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center'
    }}>
      <div style={{
        textAlign: 'center',
        color: 'var(--text-muted)',
        fontFamily: 'var(--font-body)'
      }}>
        <h1 style={{ fontSize: '24px', marginBottom: '16px', color: 'var(--text)' }}>
          FloatingChatFAB Test
        </h1>
        <p>Placeholder page for testing the FloatingChatFAB</p>
        <p style={{ marginTop: '8px' }}>Component will be implemented here</p>
      </div>
    </div>
  )
}
