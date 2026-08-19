import { useEffect, useState, type FormEvent } from 'react'
import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import { RegistrationQuestionsEditor } from '../../registration/components/RegistrationQuestionsEditor'
import { getHackathon, updateHackathon } from '../api/hackathonsApi'
import type { Hackathon, UpdateHackathonPayload } from '../types'

function toDateTimeInput(value: string) {
  const date = new Date(value)
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

function fromDateTimeInput(value: string) {
  return new Date(value).toISOString()
}

interface SettingsFormProps {
  hackathon: Hackathon
  canEdit: boolean
  onSaved: (hackathon: Hackathon) => void
}

function SettingsForm({ hackathon, canEdit, onSaved }: SettingsFormProps) {
  const [name, setName] = useState(hackathon.name)
  const [description, setDescription] = useState(hackathon.description ?? '')
  const [startDate, setStartDate] = useState(toDateTimeInput(hackathon.start_date))
  const [endDate, setEndDate] = useState(toDateTimeInput(hackathon.end_date))
  const [registrationOpensAt, setRegistrationOpensAt] = useState(
    toDateTimeInput(hackathon.registration_opens_at ?? hackathon.start_date),
  )
  const [registrationDeadline, setRegistrationDeadline] = useState(
    toDateTimeInput(hackathon.registration_deadline ?? hackathon.start_date),
  )
  const [capacity, setCapacity] = useState(
    hackathon.capacity === null ? '' : String(hackathon.capacity),
  )
  const [maxTeamSize, setMaxTeamSize] = useState(String(hackathon.max_team_size))
  const [isSaving, setIsSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!canEdit) return
    setIsSaving(true)
    setError(null)
    setSuccess(false)

    const payload: UpdateHackathonPayload = {
      name: name.trim(),
      description: description.trim(),
      start_date: fromDateTimeInput(startDate),
      end_date: fromDateTimeInput(endDate),
      registration_opens_at: fromDateTimeInput(registrationOpensAt),
      registration_deadline: fromDateTimeInput(registrationDeadline),
      capacity: capacity.trim() ? Number(capacity) : null,
      max_team_size: Number(maxTeamSize),
    }

    try {
      const updatedHackathon = await updateHackathon(hackathon.public_id, payload)
      onSaved(updatedHackathon)
      setSuccess(true)
    } catch {
      setError('Nie udało się zapisać ustawień hackathonu. Sprawdź dane i spróbuj ponownie.')
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form className="hackathon-settings-form" onSubmit={handleSubmit} noValidate>
      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert>Ustawienia hackathonu zostały zapisane.</Alert>}
      <FormField disabled={!canEdit} id="hackathon-name" label="Nazwa hackathonu" value={name} required onChange={(event) => setName(event.target.value)} />
      <div className="form-field">
        <label htmlFor="hackathon-description">Opis</label>
        <textarea disabled={!canEdit} id="hackathon-description" value={description} rows={4} onChange={(event) => setDescription(event.target.value)} />
      </div>
      <div className="hackathon-settings-grid">
        <FormField disabled={!canEdit} id="hackathon-start" label="Początek hackathonu" type="datetime-local" value={startDate} required onChange={(event) => setStartDate(event.target.value)} />
        <FormField disabled={!canEdit} id="hackathon-end" label="Koniec hackathonu" type="datetime-local" value={endDate} required onChange={(event) => setEndDate(event.target.value)} />
        <FormField disabled={!canEdit} id="registration-opens" label="Otwarcie rejestracji" type="datetime-local" value={registrationOpensAt} required onChange={(event) => setRegistrationOpensAt(event.target.value)} />
        <FormField disabled={!canEdit} id="registration-deadline" label="Koniec rejestracji" type="datetime-local" value={registrationDeadline} required onChange={(event) => setRegistrationDeadline(event.target.value)} />
        <FormField disabled={!canEdit} id="hackathon-capacity" label="Limit uczestników" type="number" min={1} value={capacity} onChange={(event) => setCapacity(event.target.value)} />
        <FormField disabled={!canEdit} id="max-team-size" label="Maksymalny rozmiar drużyny" type="number" min={1} value={maxTeamSize} required onChange={(event) => setMaxTeamSize(event.target.value)} />
      </div>
      <div className="form-actions">
        {canEdit && <Button type="submit" disabled={isSaving}>{isSaving ? 'Zapisywanie…' : 'Zapisz ustawienia'}</Button>}
      </div>
    </form>
  )
}

export function HackathonSettingsPage() {
  const navigate = useNavigate()
  const { hackathonPublicId } = useParams<{ hackathonPublicId: string }>()
  const [hackathon, setHackathon] = useState<Hackathon | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState(false)

  useEffect(() => {
    if (!hackathonPublicId) return
    void getHackathon(hackathonPublicId)
      .then(setHackathon)
      .catch(() => setError(true))
      .finally(() => setIsLoading(false))
  }, [hackathonPublicId])

  if (!hackathonPublicId) return <Navigate to="/hackathons" replace />
  if (isLoading) return <main className="app-page"><Spinner label="Ładowanie ustawień…" /></main>
  if (error || !hackathon) return <main className="app-page"><Alert variant="error">Nie udało się pobrać ustawień hackathonu.</Alert></main>

  return (
    <main className="app-page">
      <header className="page-header">
        <div>
          <h1>Ustawienia: {hackathon.name}</h1>
          <p>Zmień dane hackathonu i formularz zgłoszeniowy.</p>
        </div>
        <Button type="button" variant="ghost" onClick={() => navigate('/hackathons')}>Wróć do listy</Button>
      </header>
      <Card>
        <h2>Dane hackathonu</h2>
        {hackathon.access_level === 'co_organizer' && (
          <Alert>Podstawowe dane hackathonu może zmieniać tylko właściciel.</Alert>
        )}
        <SettingsForm
          canEdit={hackathon.access_level === 'owner'}
          hackathon={hackathon}
          onSaved={setHackathon}
        />
      </Card>
      <Card>
        <h2>Pytania rejestracyjne</h2>
        <p className="registration-questions-hint">Pytania można zmieniać tylko przed otwarciem rejestracji.</p>
        <RegistrationQuestionsEditor hackathonPublicId={hackathon.public_id} />
      </Card>
    </main>
  )
}