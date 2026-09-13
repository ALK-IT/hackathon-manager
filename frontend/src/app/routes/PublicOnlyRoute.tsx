import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { Spinner } from '../../components/ui'
import { useAuth } from '../../features/auth'
import { useTranslation } from '../../i18n/useTranslation'

export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()
  const { t } = useTranslation()

  if (isLoading) {
    return (
      <main className="centered-page">
        <Spinner label={t.checkingSession} />
      </main>
    )
  }

  if (user) return <Navigate to="/hackathons" replace />
  return children
}
