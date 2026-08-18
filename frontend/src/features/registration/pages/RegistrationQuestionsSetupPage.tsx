import { Navigate, useNavigate, useParams } from 'react-router-dom'
import { Button, Card } from '../../../components/ui'
import { RegistrationQuestionsEditor } from '../components/RegistrationQuestionsEditor'

export function RegistrationQuestionsSetupPage() {
  const navigate = useNavigate()
  const { hackathonPublicId } = useParams<{ hackathonPublicId: string }>()

  if (!hackathonPublicId) return <Navigate to="/hackathons" replace />

  return (
    <main className="app-page">
      <Card className="registration-questions-setup-card">
        <h1>Dodaj pytania rejestracyjne</h1>
        <p>
          Hackathon został utworzony. Dodaj pytania, na które uczestnicy odpowiedzą
          podczas zapisu.
        </p>
        <p className="registration-questions-hint">
          Pytania można zmieniać tylko przed otwarciem rejestracji.
        </p>
        <RegistrationQuestionsEditor hackathonPublicId={hackathonPublicId} />
        <div className="form-actions">
          <Button type="button" onClick={() => navigate('/hackathons', { replace: true })}>
            Zakończ konfigurację
          </Button>
        </div>
      </Card>
    </main>
  )
}
