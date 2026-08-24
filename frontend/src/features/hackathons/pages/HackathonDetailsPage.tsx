import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { useAuth } from '../../auth'
import { addCoOrganizer, getHackathon } from '../api/hackathonsApi'
import { CoOrganizerAutocomplete } from '../components/CoOrganizerAutocomplete'
import type { HackathonDetails, UserSummary } from '../types'
import {
  getAddCoOrganizerErrorMessage,
  getHackathonDetailsErrorMessage,
} from '../utils/hackathonMessages'

export function HackathonDetailsPage() {
  const navigate = useNavigate()
  const { hackathonPublicId } = useParams()
  const { isLoading: isAuthLoading } = useAuth()
  const [hackathon, setHackathon] = useState<HackathonDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [coOrganizerName, setCoOrganizerName] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState<UserSummary | null>(null)
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

    if (!selectedCandidate) {
      setFieldError('Wybierz użytkownika z listy podpowiedzi.')
      return
    }

    setFieldError(undefined)
    setSubmitError(null)
    setSuccessMessage(null)
    setIsSubmitting(true)

    try {
      const updatedHackathon = await addCoOrganizer(hackathonPublicId, {
        user_public_id: selectedCandidate.public_id,
      })
      const addedCoOrganizer = updatedHackathon.co_organizers.find(
        (user) => user.public_id === selectedCandidate.public_id,
      )
      setHackathon(updatedHackathon)
      setCoOrganizerName('')
      setSelectedCandidate(null)
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
                <CoOrganizerAutocomplete
                  hackathonPublicId={hackathon.public_id}
                  query={coOrganizerName}
                  selectedCandidate={selectedCandidate}
                  error={fieldError}
                  onQueryChange={(query) => {
                    setCoOrganizerName(query)
                    setSelectedCandidate(null)
                    setFieldError(undefined)
                    setSuccessMessage(null)
                  }}
                  onCandidateSelect={(candidate) => {
                    setSelectedCandidate(candidate)
                    setCoOrganizerName(candidate.name)
                    setFieldError(undefined)
                  }}
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
