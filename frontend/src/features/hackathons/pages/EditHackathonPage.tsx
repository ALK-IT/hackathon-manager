import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import { getHackathon, updateHackathon } from '../api/hackathonsApi'
import { getHackathonSettingsErrorMessage } from '../utils/hackathonMessages'
import {
  validateCreateHackathon,
  type CreateHackathonErrors,
} from '../utils/validation'

function toLocalDateTime(value: string): string {
  const date = new Date(value)
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

export function EditHackathonPage() {
  const navigate = useNavigate()
  const { hackathonPublicId } = useParams()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [registrationOpensAt, setRegistrationOpensAt] = useState('')
  const [registrationDeadline, setRegistrationDeadline] = useState('')
  const [capacity, setCapacity] = useState('')
  const [maxTeamSize, setMaxTeamSize] = useState('')
  const [errors, setErrors] = useState<CreateHackathonErrors>({})
  const [loadError, setLoadError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)

  useEffect(() => {
    const controller = new AbortController()

    async function loadHackathon() {
      if (!hackathonPublicId) {
        setLoadError('Nieprawidłowy adres hackathonu.')
        setIsLoading(false)
        return
      }

      try {
        const hackathon = await getHackathon(hackathonPublicId, controller.signal)
        setName(hackathon.name)
        setDescription(hackathon.description)
        setStartDate(toLocalDateTime(hackathon.start_date))
        setEndDate(toLocalDateTime(hackathon.end_date))
        setRegistrationOpensAt(toLocalDateTime(hackathon.registration_opens_at))
        setRegistrationDeadline(toLocalDateTime(hackathon.registration_deadline))
        setCapacity(hackathon.capacity?.toString() ?? '')
        setMaxTeamSize(hackathon.max_team_size.toString())
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
        setLoadError(getHackathonSettingsErrorMessage(error))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadHackathon()
    return () => controller.abort()
  }, [hackathonPublicId])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!hackathonPublicId) return

    const validationErrors = validateCreateHackathon({
      name,
      description,
      startDate,
      endDate,
      registrationOpensAt,
      registrationDeadline,
      capacity,
      maxTeamSize,
    })
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      await updateHackathon(hackathonPublicId, {
        name: name.trim(),
        description: description.trim(),
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        registration_opens_at: new Date(registrationOpensAt).toISOString(),
        registration_deadline: new Date(registrationDeadline).toISOString(),
        capacity: capacity ? Number(capacity) : null,
        max_team_size: Number(maxTeamSize),
      })
      navigate('/hackathons', { replace: true })
    } catch (error) {
      setSubmitError(getHackathonSettingsErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <Card className="create-hackathon-card">
        <h1>Ustawienia hackathonu</h1>
        {isLoading && <Spinner label="Ładowanie ustawień…" />}
        {loadError && <Alert variant="error">{loadError}</Alert>}

        {!isLoading && !loadError && (
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <FormField
              id="hackathon-name"
              label="Nazwa"
              value={name}
              error={errors.name}
              maxLength={200}
              required
              onChange={(event) => setName(event.target.value)}
            />
            <FormField
              id="hackathon-description"
              label="Opis"
              value={description}
              error={errors.description}
              maxLength={5000}
              onChange={(event) => setDescription(event.target.value)}
            />
            <FormField
              id="hackathon-start-date"
              label="Rozpoczęcie hackathonu"
              type="datetime-local"
              value={startDate}
              error={errors.startDate}
              required
              onChange={(event) => setStartDate(event.target.value)}
            />
            <FormField
              id="hackathon-end-date"
              label="Zakończenie hackathonu"
              type="datetime-local"
              value={endDate}
              error={errors.endDate}
              required
              onChange={(event) => setEndDate(event.target.value)}
            />
            <FormField
              id="registration-opens-at"
              label="Otwarcie zapisów"
              type="datetime-local"
              value={registrationOpensAt}
              error={errors.registrationOpensAt}
              required
              onChange={(event) => setRegistrationOpensAt(event.target.value)}
            />
            <FormField
              id="registration-deadline"
              label="Zamknięcie zapisów"
              type="datetime-local"
              value={registrationDeadline}
              error={errors.registrationDeadline}
              required
              onChange={(event) => setRegistrationDeadline(event.target.value)}
            />
            <FormField
              id="hackathon-capacity"
              label="Limit uczestników (opcjonalny)"
              type="number"
              min="1"
              value={capacity}
              error={errors.capacity}
              onChange={(event) => setCapacity(event.target.value)}
            />
            <FormField
              id="hackathon-max-team-size"
              label="Maksymalna wielkość drużyny"
              type="number"
              min="1"
              value={maxTeamSize}
              error={errors.maxTeamSize}
              required
              onChange={(event) => setMaxTeamSize(event.target.value)}
            />
            {submitError && <Alert variant="error">{submitError}</Alert>}
            <div className="form-actions">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Zapisywanie…' : 'Zapisz ustawienia'}
              </Button>
              <Button type="button" variant="ghost" onClick={() => navigate('/hackathons')}>
                Anuluj
              </Button>
            </div>
          </form>
        )}
      </Card>
    </main>
  )
}
