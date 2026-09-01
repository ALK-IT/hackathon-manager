import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import {
  getManagedRegistrations,
  updateManagedRegistration,
  type ManagedRegistration,
  type ManagedStatus,
} from '../managementApi'
import {
  getManagedRegistrationsErrorMessage,
  getManagedRegistrationStatusErrorMessage,
  isRegistrationStatusChangeLockedError,
} from '../utils/registrationMessages'

const PAGE_SIZE = 50

const labels: Record<ManagedStatus, string> = {
  pending: 'oczekujące',
  accepted: 'zaakceptowane',
  rejected: 'odrzucone',
}

export function ManageRegistrationsPage() {
  const { hackathonPublicId } = useParams()
  const [registrations, setRegistrations] = useState<ManagedRegistration[]>([])
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [updating, setUpdating] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [actionError, setActionError] = useState<string | null>(null)
  const [page, setPage] = useState(0)
  const [hasNextPage, setHasNextPage] = useState(false)
  const [reloadKey, setReloadKey] = useState(0)
  const [statusChangesLocked, setStatusChangesLocked] = useState(false)
  const selected = registrations.find(({ public_id }) => public_id === selectedId)

  useEffect(() => {
    if (!hackathonPublicId) return
    const controller = new AbortController()
    setLoading(true)
    setLoadError(null)
    setRegistrations([])
    setHasNextPage(false)
    setSelectedId(null)
    getManagedRegistrations(hackathonPublicId, {
      limit: PAGE_SIZE + 1,
      offset: page * PAGE_SIZE,
      signal: controller.signal,
    })
      .then((result) => {
        setRegistrations(result.slice(0, PAGE_SIZE))
        setHasNextPage(result.length > PAGE_SIZE)
      })
      .catch((requestError: unknown) => {
        if (!(requestError instanceof Error && requestError.name === 'AbortError')) {
          setLoadError(getManagedRegistrationsErrorMessage(requestError))
        }
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [hackathonPublicId, page, reloadKey])

  async function changeStatus(status: 'accepted' | 'rejected') {
    if (!selected) return
    setUpdating(true)
    setActionError(null)
    try {
      const updated = await updateManagedRegistration(selected.public_id, status)
      setRegistrations((current) =>
        current.map((registration) =>
          registration.public_id === selected.public_id
            ? { ...registration, ...updated }
            : registration,
        ),
      )
    } catch (requestError) {
      setActionError(getManagedRegistrationStatusErrorMessage(requestError))
      if (isRegistrationStatusChangeLockedError(requestError)) {
        setStatusChangesLocked(true)
      }
      setReloadKey((current) => current + 1)
    } finally {
      setUpdating(false)
    }
  }

  return (
    <main className="app-page">
      <Link to="/hackathons">Wróć do hackathonów</Link>
      <h1>Zgłoszenia</h1>
      {loading && <Spinner label="Ładowanie zgłoszeń…" />}
      {loadError && <Alert variant="error">{loadError}</Alert>}
      {actionError && <Alert variant="error">{actionError}</Alert>}
      {!loading && registrations.length === 0 && <p>Brak zgłoszeń.</p>}
      <div className="hackathon-details-stack">
        {registrations.length > 0 && (
          <Card>
            <ul>
              {registrations.map((registration) => (
                <li key={registration.public_id}>
                  {registration.user.name} — {labels[registration.status]}{' '}
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() => setSelectedId(registration.public_id)}
                  >
                    Obejrzyj zgłoszenie
                  </Button>
                </li>
              ))}
            </ul>
            <nav aria-label="Stronicowanie zgłoszeń">
              <Button
                type="button"
                variant="ghost"
                disabled={loading || page === 0}
                onClick={() => setPage((current) => current - 1)}
              >
                Poprzednia strona
              </Button>
              <span aria-live="polite">Strona {page + 1}</span>
              <Button
                type="button"
                variant="ghost"
                disabled={loading || !hasNextPage}
                onClick={() => setPage((current) => current + 1)}
              >
                Następna strona
              </Button>
            </nav>
          </Card>
        )}
        {selected && (
          <Card>
            <h2>{selected.user.name}</h2>
            <p>{selected.user.email}</p>
            <p>Status: {labels[selected.status]}</p>
            {selected.team && <p>Drużyna: {selected.team.name}</p>}
            <h3>Odpowiedzi</h3>
            {selected.answers.length === 0 && <p>Brak odpowiedzi.</p>}
            {selected.answers.map((answer) => (
              <div key={answer.question.public_id}>
                <strong>{answer.question.content}</strong>
                <p>{answer.content}</p>
              </div>
            ))}
            <Button
              type="button"
              disabled={
                updating || statusChangesLocked || selected.status === 'accepted'
              }
              onClick={() => changeStatus('accepted')}
            >
              Akceptuj
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={
                updating || statusChangesLocked || selected.status === 'rejected'
              }
              onClick={() => changeStatus('rejected')}
            >
              Odrzuć
            </Button>
          </Card>
        )}
      </div>
    </main>
  )
}
