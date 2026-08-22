import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { getHackathon, updateHackathon } from '../api/hackathonsApi'

type Form = Record<
  | 'name'
  | 'description'
  | 'startDate'
  | 'endDate'
  | 'registrationOpensAt'
  | 'registrationDeadline'
  | 'capacity'
  | 'maxTeamSize',
  string
>

const fields: Array<[keyof Form, string, string]> = [
  ['name', 'Nazwa', 'text'],
  ['description', 'Opis', 'text'],
  ['startDate', 'Rozpoczęcie hackathonu', 'datetime-local'],
  ['endDate', 'Zakończenie hackathonu', 'datetime-local'],
  ['registrationOpensAt', 'Otwarcie zapisów', 'datetime-local'],
  ['registrationDeadline', 'Zamknięcie zapisów', 'datetime-local'],
  ['capacity', 'Limit uczestników (opcjonalny)', 'number'],
  ['maxTeamSize', 'Maksymalna wielkość drużyny', 'number'],
]

const localDate = (value: string) => {
  const date = new Date(value)
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 16)
}

export function EditHackathonPage() {
  const { hackathonPublicId } = useParams()
  const navigate = useNavigate()
  const [form, setForm] = useState<Form | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [saving, setSaving] = useState(false)

  useEffect(() => {
    if (!hackathonPublicId) return
    const controller = new AbortController()
    getHackathon(hackathonPublicId, controller.signal)
      .then((hackathon) =>
        setForm({
          name: hackathon.name,
          description: hackathon.description,
          startDate: localDate(hackathon.start_date),
          endDate: localDate(hackathon.end_date),
          registrationOpensAt: localDate(hackathon.registration_opens_at),
          registrationDeadline: localDate(hackathon.registration_deadline),
          capacity: hackathon.capacity?.toString() ?? '',
          maxTeamSize: hackathon.max_team_size.toString(),
        }),
      )
      .catch((requestError: unknown) => {
        if (!(requestError instanceof Error && requestError.name === 'AbortError')) {
          setError('Nie udało się pobrać ustawień hackathonu.')
        }
      })
    return () => controller.abort()
  }, [hackathonPublicId])

  async function save(event: FormEvent) {
    event.preventDefault()
    if (!form || !hackathonPublicId) return
    setSaving(true)
    setError(null)
    try {
      await updateHackathon(hackathonPublicId, {
        name: form.name.trim(),
        description: form.description.trim(),
        start_date: new Date(form.startDate).toISOString(),
        end_date: new Date(form.endDate).toISOString(),
        registration_opens_at: new Date(form.registrationOpensAt).toISOString(),
        registration_deadline: new Date(form.registrationDeadline).toISOString(),
        capacity: form.capacity ? Number(form.capacity) : null,
        max_team_size: Number(form.maxTeamSize),
      })
      navigate(`/hackathons/${hackathonPublicId}`, { replace: true })
    } catch {
      setError('Nie udało się zapisać ustawień hackathonu.')
    } finally {
      setSaving(false)
    }
  }

  return (
    <main className="app-page">
      <Card className="create-hackathon-card">
        <h1>Ustawienia hackathonu</h1>
        {!form && !error && <Spinner label="Ładowanie ustawień…" />}
        {error && <Alert variant="error">{error}</Alert>}
        {form && (
          <form className="auth-form" onSubmit={save}>
            {fields.map(([name, label, type]) => (
              <label className="form-field" key={name}>
                {label}
                <input
                  type={type}
                  value={form[name]}
                  required={name !== 'description' && name !== 'capacity'}
                  min={type === 'number' ? 1 : undefined}
                  onChange={(event) => setForm({ ...form, [name]: event.target.value })}
                />
              </label>
            ))}
            <div className="form-actions">
              <Button type="submit" disabled={saving}>
                {saving ? 'Zapisywanie…' : 'Zapisz ustawienia'}
              </Button>
              <Button type="button" variant="ghost" onClick={() => navigate(-1)}>
                Anuluj
              </Button>
            </div>
          </form>
        )}
      </Card>
    </main>
  )
}
