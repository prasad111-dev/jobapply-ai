import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'
import Navbar from '@/components/Navbar'
import Background from '@/components/Background'
import { Toaster } from 'react-hot-toast'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'JobApply AI - Apply to Multiple Jobs at Once',
  description: 'Unified job application platform with AI-powered form filling',
}

export default function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="en" className="scroll-smooth">
      <body className={inter.className}>
        <Background />
        <Toaster
          position="top-center"
          toastOptions={{
            style: {
              background: '#12172b',
              color: '#f1f5f9',
              border: '1px solid rgba(255,255,255,0.1)',
              backdropFilter: 'blur(12px)',
              borderRadius: '12px',
            },
          }}
        />
        <Navbar />
        <main className="min-h-screen">{children}</main>
      </body>
    </html>
  )
}