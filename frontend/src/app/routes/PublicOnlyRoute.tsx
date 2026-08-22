import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { Spinner } from '../../components/ui'
import { useAuth } from '../../features/auth'

export function PublicOnlyRoute({ children }: { children: ReactNode }) {
  const { user, isLoading } = useAuth()

  if (isLoading) {
    return (
      <main className="centered-page">
        <Spinner label="Sprawdzanie sesji…" />
      </main>
    )
  }

  if (user) return <Navigate to="/hackathons" replace />
  return children
}
