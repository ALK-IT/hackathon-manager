import { useEffect, useState, type ReactNode } from 'react'
import { Navigate, useParams } from 'react-router-dom'
import { Alert, Button, Spinner } from '../../components/ui'
import { useAuth } from '../../features/auth'
import { getHackathon } from '../../features/hackathons/api/hackathonsApi'
import { ApiError } from '../../lib/api/client'

export function RequireHackathonManager({ children }: { children: ReactNode }) {
  const { hackathonPublicId } = useParams()
  const { user, isLoading } = useAuth()

  if (isLoading) return <Spinner label="Sprawdzanie sesji…" />
  if (!user) return <Navigate to="/login" replace />
  if (!hackathonPublicId) return <Alert variant="error">Nieprawidłowy adres hackathonu.</Alert>

  return (
    <ManagerCheck
      key={`${hackathonPublicId}:${user.public_id}:${user.role}`}
      publicId={hackathonPublicId}
      isAdmin={user.role === 'admin'}
    >
      {children}
    </ManagerCheck>
  )
}

function ManagerCheck({ publicId, isAdmin, children }: {
  publicId: string
  isAdmin: boolean
  children: ReactNode
}) {
  const [allowed, setAllowed] = useState<boolean | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [attempt, setAttempt] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setAllowed(null)
    setError(null)
    void getHackathon(publicId, controller.signal).then((hackathon) => {
      if (!controller.signal.aborted) {
        setAllowed(isAdmin || hackathon.access_level === 'owner' ||
          hackathon.access_level === 'co_organizer')
      }
    }).catch((cause) => {
      if (controller.signal.aborted) return
      setError(cause instanceof ApiError && cause.status === 404
        ? 'Nie znaleziono hackathonu.'
        : 'Nie udało się sprawdzić uprawnień. Spróbuj ponownie.')
    })
    return () => controller.abort()
  }, [publicId, isAdmin, attempt])

  if (error) return (
    <main className="app-page">
      <Alert variant="error">{error}</Alert>
      <Button variant="ghost" onClick={() => setAttempt((value) => value + 1)}>
        Spróbuj ponownie
      </Button>
    </main>
  )
  if (allowed === null) return <Spinner label="Sprawdzanie uprawnień…" />
  if (!allowed) return <Navigate to={`/hackathons/${encodeURIComponent(publicId)}`} replace />
  return children
}
