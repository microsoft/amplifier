import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'SpaceApp Marketing',
  description: 'Marketing site for SpaceApp',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body>{children}</body>
    </html>
  )
}
