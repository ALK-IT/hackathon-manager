import type { ReactNode } from 'react'
import { Link } from 'react-router-dom'
import { Card } from '../../../components/ui'

interface AuthPageLayoutProps {
  title: string
  children: ReactNode
  footerText: string
  footerLinkText: string
  footerLinkTo: string
}

export function AuthPageLayout({
  title,
  children,
  footerText,
  footerLinkText,
  footerLinkTo,
}: AuthPageLayoutProps) {
  return (
    <main className="auth-page">
      <Card className="auth-card">
        <h1>{title}</h1>
        {children}
        <p>
          {footerText} <Link to={footerLinkTo}>{footerLinkText}</Link>
        </p>
      </Card>
    </main>
  )
}
