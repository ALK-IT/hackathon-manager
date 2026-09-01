import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Card, Spinner } from '../../../components/ui'
import { getHackathon, updateHackathon } from '../api/hackathonsApi'
import { HackathonForm, type NormalizedHackathonValues } from '../components/HackathonForm'
import {
  getHackathonDetailsErrorMessage,
  getUpdateHackathonErrorMessage,
} from '../utils/hackathonMessages'
import type { HackathonFormValues } from '../utils/validation'

const localDate = (value: string) => {
  const date = new Date(value)
  return new Date(date.getTime() - date.getTimezoneOffset() * 60_000)
    .toISOString()
    .slice(0, 16)
}

export function EditHackathonPage() {
  const { hackathonPublicId } = useParams()
  const navigate = useNavigate()
  const [form, setForm] = useState<HackathonFormValues | null>(null)
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
          setError(getHackathonDetailsErrorMessage(requestError))
        }
      })
    return () => controller.abort()
  }, [hackathonPublicId])

  async function save(values: NormalizedHackathonValues) {
    if (!hackathonPublicId || !values.registration_deadline) return
    setSaving(true)
    setError(null)
    try {
      await updateHackathon(hackathonPublicId, {
        ...values,
        registration_deadline: values.registration_deadline,
      })
      navigate(`/hackathons/${hackathonPublicId}`, { replace: true })
    } catch (requestError) {
      setError(getUpdateHackathonErrorMessage(requestError))
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
          <HackathonForm
            initialValues={form}
            isSubmitting={saving}
            submitLabel="Zapisz ustawienia"
            submittingLabel="Zapisywanie…"
            registrationDeadlineRequired
            onSubmit={save}
            onCancel={() => navigate(-1)}
          />
        )}
      </Card>
    </main>
  )
}
