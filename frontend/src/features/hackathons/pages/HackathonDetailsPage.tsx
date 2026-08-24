import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { useAuth } from '../../auth'
import { FormField } from '../../auth/components/FormField'
import {
  addCoOrganizer,
  getHackathon,
  searchCoOrganizerCandidates,
} from '../api/hackathonsApi'
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
  const [candidates, setCandidates] = useState<UserSummary[]>([])
  const [isSearchingCandidates, setIsSearchingCandidates] = useState(false)
  const [candidateSearchError, setCandidateSearchError] = useState<string | null>(null)
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

  useEffect(() => {
    const normalizedName = coOrganizerName.trim()
    if (
      !hackathonPublicId ||
      hackathon?.access_level !== 'owner' ||
      normalizedName.length < 2 ||
      selectedCandidate?.name === coOrganizerName
    ) {
      setCandidates([])
      setCandidateSearchError(null)
      setIsSearchingCandidates(false)
      return
    }

    const controller = new AbortController()
    const timeoutId = window.setTimeout(async () => {
      setIsSearchingCandidates(true)
      setCandidateSearchError(null)

      try {
        const results = await searchCoOrganizerCandidates(
          hackathonPublicId,
          normalizedName,
          controller.signal,
        )
        setCandidates(results)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
        setCandidates([])
        setCandidateSearchError('Nie udało się wyszukać użytkowników.')
      } finally {
        if (!controller.signal.aborted) setIsSearchingCandidates(false)
      }
    }, 300)

    return () => {
      window.clearTimeout(timeoutId)
      controller.abort()
    }
  }, [coOrganizerName, hackathon?.access_level, hackathonPublicId, selectedCandidate])

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
      setCandidates([])
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
                  id="co-organizer-name"
                  label="Nazwa użytkownika"
                  value={coOrganizerName}
                  error={fieldError}
                  placeholder="Zacznij wpisywać imię i nazwisko"
                  autoComplete="off"
                  role="combobox"
                  aria-autocomplete="list"
                  aria-controls="co-organizer-candidates"
                  aria-expanded={candidates.length > 0}
                  required
                  onChange={(event) => {
                    setCoOrganizerName(event.target.value)
                    setSelectedCandidate(null)
                    setFieldError(undefined)
                    setSuccessMessage(null)
                  }}
                />
                {isSearchingCandidates && <p role="status">Wyszukiwanie…</p>}
                {candidateSearchError && (
                  <Alert variant="error">{candidateSearchError}</Alert>
                )}
                {candidates.length > 0 && (
                  <ul
                    id="co-organizer-candidates"
                    className="co-organizer-candidates"
                    role="listbox"
                  >
                    {candidates.map((candidate) => (
                      <li key={candidate.public_id}>
                        <button
                          type="button"
                          role="option"
                          aria-selected={selectedCandidate?.public_id === candidate.public_id}
                          onClick={() => {
                            setSelectedCandidate(candidate)
                            setCoOrganizerName(candidate.name)
                            setCandidates([])
                            setFieldError(undefined)
                          }}
                        >
                          {candidate.name}
                        </button>
                      </li>
                    ))}
                  </ul>
                )}
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
