import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router-dom'
import { Spinner } from '../../components/ui'
import { useAuth } from '../../features/auth'
import { useTranslation } from '../../i18n/useTranslation'

export function ProtectedRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()
  const { t } = useTranslation()
  const location = useLocation()

  if (isLoading) {
    return (
      <main className="centered-page">
        <Spinner label={t.checkingSession} />
      </main>
    )
  }

  if (!user) {
    return <Navigate to="/login" replace state={{ from: location.pathname }} />
  }

  return children
}
