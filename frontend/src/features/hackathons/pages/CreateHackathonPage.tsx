import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, Card } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import { createHackathon } from '../api/hackathonsApi'
import { getCreateHackathonErrorMessage } from '../utils/hackathonMessages'
import {
  validateCreateHackathon,
  type CreateHackathonErrors,
} from '../utils/validation'

function toLocalDateTime(date: Date): string {
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

export function CreateHackathonPage() {
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [startDate, setStartDate] = useState('')
  const [endDate, setEndDate] = useState('')
  const [registrationOpensAt, setRegistrationOpensAt] = useState('')
  const [registrationDeadline, setRegistrationDeadline] = useState('')
  const [capacity, setCapacity] = useState('')
  const [maxTeamSize, setMaxTeamSize] = useState('4')
  const [errors, setErrors] = useState<CreateHackathonErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
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
      const hackathon = await createHackathon({
        name: name.trim(),
        description: description.trim(),
        start_date: new Date(startDate).toISOString(),
        end_date: new Date(endDate).toISOString(),
        registration_opens_at: new Date(registrationOpensAt).toISOString(),
        ...(registrationDeadline && {
          registration_deadline: new Date(registrationDeadline).toISOString(),
        }),
        ...(capacity && { capacity: Number(capacity) }),
        max_team_size: Number(maxTeamSize),
      })
      navigate(`/hackathons/${hackathon.public_id}/questions/setup`, {
        replace: true,
      })
    } catch (error) {
      setSubmitError(getCreateHackathonErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <Card className="create-hackathon-card">
        <h1>Utwórz hackathon</h1>
        {submitError && <Alert variant="error">{submitError}</Alert>}
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
          <div className="registration-opening-field">
            <FormField
              id="registration-opens-at"
              label="Otwarcie zapisów"
              type="datetime-local"
              value={registrationOpensAt}
              error={errors.registrationOpensAt}
              required
              onChange={(event) => setRegistrationOpensAt(event.target.value)}
            />
            <Button
              type="button"
              variant="ghost"
              onClick={() => setRegistrationOpensAt(toLocalDateTime(new Date()))}
            >
              Teraz
            </Button>
          </div>
          <FormField
            id="registration-deadline"
            label="Zamknięcie zapisów (opcjonalne)"
            type="datetime-local"
            value={registrationDeadline}
            error={errors.registrationDeadline}
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
          <div className="form-actions">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Tworzenie…' : 'Utwórz hackathon'}
            </Button>
            <Button type="button" variant="ghost" onClick={() => navigate('/hackathons')}>
              Anuluj
            </Button>
          </div>
        </form>
      </Card>
    </main>
  )
}
