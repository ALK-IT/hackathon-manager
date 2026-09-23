import { useEffect, useState, type FormEvent } from 'react'
import { Link, useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Countdown, Spinner } from '../../../components/ui'
import { AttendanceQrGenerator } from '../../attendance'
import { useHasEnded } from '../../evaluations/utils'
import { useAuth } from '../../auth'
import { useTranslation } from '../../../i18n/useTranslation'
import { addCoOrganizer, getHackathon } from '../api/hackathonsApi'
import { CoOrganizerAutocomplete } from '../components/CoOrganizerAutocomplete'
import { HackathonTaskManager } from '../components/HackathonTaskManager'
import type { HackathonDetails, UserSummary } from '../types'
import {
  getAddCoOrganizerErrorMessage,
  getHackathonDetailsErrorMessage,
} from '../utils/hackathonMessages'
import { isHackathonInProgress } from '../utils/hackathonTime'

export function HackathonDetailsPage() {
  const { language, t } = useTranslation()
  const navigate = useNavigate()
  const { hackathonPublicId } = useParams()
  const { user, isLoading: isAuthLoading } = useAuth()
  const [hackathon, setHackathon] = useState<HackathonDetails | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [coOrganizerName, setCoOrganizerName] = useState('')
  const [selectedCandidate, setSelectedCandidate] = useState<UserSummary | null>(null)
  const [fieldError, setFieldError] = useState<string | undefined>()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const hasEnded = useHasEnded(hackathon?.end_date ?? '')

  useEffect(() => {
    const controller = new AbortController()

    async function loadHackathon() {
      if (isAuthLoading) return

      if (!hackathonPublicId) {
        setLoadError(language === 'en' ? 'Invalid hackathon address.' : 'Nieprawidłowy adres hackathonu.')
        setIsLoading(false)
        return
      }

      try {
        setHackathon(await getHackathon(hackathonPublicId, controller.signal))
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
          setLoadError(getHackathonDetailsErrorMessage(error, language))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadHackathon()
    return () => controller.abort()
  }, [hackathonPublicId, isAuthLoading, language])

  async function handleAddCoOrganizer(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!hackathonPublicId || !hackathon || hackathon.access_level !== 'owner') return

    if (!selectedCandidate) {
      setFieldError(language === 'en' ? 'Select a user from the suggestions.' : 'Wybierz użytkownika z listy podpowiedzi.')
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
          : language === 'en' ? 'Co-organizer added.' : 'Dodano współorganizatora.',
      )
    } catch (error) {
      setSubmitError(getAddCoOrganizerErrorMessage(error, language))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <div className="details-back-link">
        <Link to="/hackathons">{t.backToList}</Link>
      </div>

      {isLoading && <Spinner label={t.loadingDetails} />}
      {loadError && <Alert variant="error">{loadError}</Alert>}

      {hackathon && (
        <div className="hackathon-details-stack">
          <Card>
            <h1>{hackathon.name}</h1>
            {hackathon.description && <p>{hackathon.description}</p>}
            <p>
              {t.term}: {new Date(hackathon.start_date).toLocaleString(language === 'en' ? 'en-US' : 'pl-PL')} –{' '}
              {new Date(hackathon.end_date).toLocaleString(language === 'en' ? 'en-US' : 'pl-PL')}
            </p>
            <Countdown startDate={hackathon.start_date} endDate={hackathon.end_date} language={language} />
            <p>{t.registration}: {hackathon.registration_open ? t.registrationOpen : t.registrationClosed}</p>
            <p>{t.organizer}: {hackathon.organizer.name}</p>
            <p>
              Maksymalna wielkość drużyny: {hackathon.max_team_size}
            </p>
            {hackathon.capacity !== null && <p>{t.participantLimitLabel}: {hackathon.capacity}</p>}
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
            <h2>{t.coOrganizers}</h2>
            {hackathon.co_organizers.length === 0 ? (
              <p>{t.noCoOrganizers}</p>
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
                  {isSubmitting ? t.adding : t.addCoOrganizer}
                </Button>
              </form>
            )}
          </Card>

          {(hackathon.access_level === 'owner' ||
            hackathon.access_level === 'co_organizer') && (
            <Card>
              <HackathonTaskManager
                hackathonPublicId={hackathon.public_id}
                hackathonStartDate={hackathon.start_date}
                hackathonEndDate={hackathon.end_date}
              />
            </Card>
          )}

          {isHackathonInProgress(hackathon.start_date, hackathon.end_date) &&
            (user?.role === 'admin' ||
              hackathon.access_level === 'owner' ||
              hackathon.access_level === 'co_organizer') && (
              <Card>
                <AttendanceQrGenerator
                  hackathonPublicId={hackathon.public_id}
                />
                <div className="attendance-participants-link">
                  <Button
                    type="button"
                    variant="ghost"
                    onClick={() =>
                      navigate(
                        `/hackathons/${hackathon.public_id}/attendance`,
                      )
                    }
                  >
                    Pokaż uczestników
                  </Button>
                </div>
              </Card>
            )}
          {hasEnded && (user?.role === 'admin' || hackathon.access_level === 'owner' ||
            hackathon.access_level === 'co_organizer') && (
            <Card>
              <Link to={`/hackathons/${hackathon.public_id}/solutions`}>Oceń rozwiązania</Link>
            </Card>
          )}
        </div>
      )}
    </main>
  )
}
