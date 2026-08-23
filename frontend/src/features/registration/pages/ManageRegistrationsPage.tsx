import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import {
  getManagedRegistrations,
  updateManagedRegistration,
  type ManagedRegistration,
  type ManagedStatus,
} from '../managementApi'

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
  const [error, setError] = useState<string | null>(null)
  const selected = registrations.find(({ public_id }) => public_id === selectedId)

  useEffect(() => {
    if (!hackathonPublicId) return
    getManagedRegistrations(hackathonPublicId)
      .then(setRegistrations)
      .catch(() => setError('Nie udało się pobrać zgłoszeń.'))
      .finally(() => setLoading(false))
  }, [hackathonPublicId])

  async function changeStatus(status: 'accepted' | 'rejected') {
    if (!selected) return
    setUpdating(true)
    setError(null)
    try {
      const updated = await updateManagedRegistration(selected.public_id, status)
      setRegistrations((current) =>
        current.map((registration) =>
          registration.public_id === selected.public_id
            ? { ...registration, ...updated }
            : registration,
        ),
      )
    } catch {
      setError('Nie udało się zmienić statusu zgłoszenia.')
    } finally {
      setUpdating(false)
    }
  }

  return (
    <main className="app-page">
      <Link to="/hackathons">Wróć do hackathonów</Link>
      <h1>Zgłoszenia</h1>
      {loading && <Spinner label="Ładowanie zgłoszeń…" />}
      {error && <Alert variant="error">{error}</Alert>}
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
              disabled={updating || selected.status === 'accepted'}
              onClick={() => changeStatus('accepted')}
            >
              Akceptuj
            </Button>
            <Button
              type="button"
              variant="ghost"
              disabled={updating || selected.status === 'rejected'}
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
