import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Card } from '../../../components/ui'
import { createHackathon } from '../api/hackathonsApi'
import { HackathonForm, type NormalizedHackathonValues } from '../components/HackathonForm'
import { getCreateHackathonErrorMessage } from '../utils/hackathonMessages'

const initialValues = {
  name: '',
  description: '',
  startDate: '',
  endDate: '',
  registrationOpensAt: '',
  registrationDeadline: '',
  capacity: '',
  maxTeamSize: '4',
}

export function CreateHackathonPage() {
  const navigate = useNavigate()
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(values: NormalizedHackathonValues) {
    setSubmitError(null)
    setIsSubmitting(true)

    try {
      const { registration_deadline, capacity, ...requiredValues } = values
      const hackathon = await createHackathon({
        ...requiredValues,
        ...(registration_deadline && { registration_deadline }),
        ...(capacity !== null && { capacity }),
      })
      navigate(`/hackathons/${hackathon.public_id}/questions/setup`, { replace: true })
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
        <HackathonForm
          initialValues={initialValues}
          isSubmitting={isSubmitting}
          submitLabel="Utwórz hackathon"
          submittingLabel="Tworzenie…"
          onSubmit={handleSubmit}
          onCancel={() => navigate('/hackathons')}
        />
      </Card>
    </main>
  )
}
