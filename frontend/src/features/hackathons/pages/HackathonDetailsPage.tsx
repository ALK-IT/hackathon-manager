import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { useAuth } from '../../auth'
import { FormField } from '../../auth/components/FormField'
import { addCoOrganizer, getHackathon } from '../api/hackathonsApi'
import type { HackathonDetails } from '../types'
import {
  getAddCoOrganizerErrorMessage,
  getHackathonDetailsErrorMessage,
} from '../utils/hackathonMessages'

const uuidPattern =
  /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i

export function HackathonDetailsPage() {
  const navigate = useNavigate()
  const { hackathonPublicId } = useParams()
  const { isLoading: isAuthLoading } = useAuth()
  const [hackathon, setHackathon] = useState<HackathonDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [coOrganizerPublicId, setCoOrganizerPublicId] = useState('')
  const [fieldError, setFieldError] = useState<string | undefined>()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    const controller = new AbortController()

    async function loadHackathon() {
      if (isAuthLoading) return

      if (!hackathonPublicId) {
        setLoadError('Nieprawidłowy adres hackathonu.')
        setIsLoading(false)
        return
      }

      try {
        setHackathon(await getHackathon(hackathonPublicId, controller.signal))
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
        setLoadError(getHackathonDetailsErrorMessage(error))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadHackathon()
    return () => controller.abort()
  }, [hackathonPublicId, isAuthLoading])

  async function handleAddCoOrganizer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!hackathonPublicId || !hackathon || hackathon.access_level !== 'owner') return

    const normalizedPublicId = coOrganizerPublicId.trim()
    if (!uuidPattern.test(normalizedPublicId)) {
      setFieldError('Podaj poprawne public_id użytkownika.')
      return
    }

    setFieldError(undefined)
    setSubmitError(null)
    setSuccessMessage(null)
    setIsSubmitting(true)

    try {
      const updatedHackathon = await addCoOrganizer(hackathonPublicId, {
        user_public_id: normalizedPublicId,
      })
      const addedCoOrganizer = updatedHackathon.co_organizers.find(
        (user) => user.public_id === normalizedPublicId,
      )
      setHackathon(updatedHackathon)
      setCoOrganizerPublicId('')
      setSuccessMessage(
        addedCoOrganizer
          ? `Dodano współorganizatora: ${addedCoOrganizer.name}.`
          : 'Dodano współorganizatora.',
      )
    } catch (error) {
      setSubmitError(getAddCoOrganizerErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <div className="details-back-link">
        <Link to="/hackathons">Wróć do listy hackathonów</Link>
      </div>

      {isLoading && <Spinner label="Ładowanie szczegółów hackathonu…" />}
      {loadError && <Alert variant="error">{loadError}</Alert>}

      {hackathon && (
        <div className="hackathon-details-stack">
          <Card>
            <h1>{hackathon.name}</h1>
            {hackathon.description && <p>{hackathon.description}</p>}
            <p>
              Termin: {new Date(hackathon.start_date).toLocaleString('pl-PL')} –{' '}
              {new Date(hackathon.end_date).toLocaleString('pl-PL')}
            </p>
            <p>Rejestracja: {hackathon.registration_open ? 'otwarta' : 'zamknięta'}</p>
            <p>Organizator: {hackathon.organizer.name}</p>
            <p>
              Maksymalna wielkość drużyny: {hackathon.max_team_size}
            </p>
            {hackathon.capacity !== null && <p>Limit uczestników: {hackathon.capacity}</p>}
            {hackathon.registration_open && (
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate(`/hackathons/${hackathon.public_id}/register`)}
              >
                Zarejestruj się
              </Button>
            )}
          </Card>

          <Card>
            <h2>Współorganizatorzy</h2>
            {hackathon.co_organizers.length === 0 ? (
              <p>Brak współorganizatorów.</p>
            ) : (
              <ul className="co-organizer-list">
                {hackathon.co_organizers.map((coOrganizer) => (
                  <li key={coOrganizer.public_id}>{coOrganizer.name}</li>
                ))}
              </ul>
            )}

            {hackathon.access_level === 'owner' && (
              <form className="co-organizer-form" onSubmit={handleAddCoOrganizer} noValidate>
                <FormField
                  id="co-organizer-public-id"
                  label="Public ID użytkownika"
                  value={coOrganizerPublicId}
                  error={fieldError}
                  placeholder="00000000-0000-0000-0000-000000000000"
                  required
                  onChange={(event) => setCoOrganizerPublicId(event.target.value)}
                />
                {submitError && <Alert variant="error">{submitError}</Alert>}
                {successMessage && <Alert>{successMessage}</Alert>}
                <Button type="submit" variant="ghost" disabled={isSubmitting}>
                  {isSubmitting ? 'Dodawanie…' : 'Dodaj współorganizatora'}
                </Button>
              </form>
            )}
          </Card>
        </div>
      )}
    </main>
  )
}
