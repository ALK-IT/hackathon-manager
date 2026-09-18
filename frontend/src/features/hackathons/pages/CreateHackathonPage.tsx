import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button, Card } from '../../../components/ui'
import { createHackathon } from '../api/hackathonsApi'
import { HackathonForm, type NormalizedHackathonValues } from '../components/HackathonForm'
import { getCreateHackathonErrorMessage } from '../utils/hackathonMessages'
import { useTranslation } from '../../../i18n/useTranslation'

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

interface EditableQuestion {
  localId: string
  content: string
  is_required: boolean
}

function createQuestion(): EditableQuestion {
  return { localId: crypto.randomUUID(), content: '', is_required: true }
}

export function CreateHackathonPage() {
  const { language, t } = useTranslation()
  const navigate = useNavigate()
  const [questions, setQuestions] = useState<EditableQuestion[]>(() => [createQuestion()])
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(values: NormalizedHackathonValues) {
    const normalizedQuestions = questions.map(({ content, is_required }) => ({
      content: content.trim(),
      is_required,
    }))
    if (normalizedQuestions.some(({ content }) => !content)) {
      setSubmitError('Uzupełnij treść każdego pytania.')
      return
    }

    setSubmitError(null)
    setIsSubmitting(true)

    try {
      const { registration_deadline, capacity, ...requiredValues } = values
      const hackathon = await createHackathon({
        ...requiredValues,
        ...(registration_deadline && { registration_deadline }),
        ...(capacity !== null && { capacity }),
        questions: normalizedQuestions,
      })
      navigate(`/hackathons/${hackathon.public_id}`, { replace: true })
    } catch (error) {
      setSubmitError(getCreateHackathonErrorMessage(error, language))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <Card className="create-hackathon-card">
        <h1>{t.createHackathon}</h1>
        {submitError && <Alert variant="error">{submitError}</Alert>}
        <HackathonForm
          initialValues={initialValues}
          isSubmitting={isSubmitting}
          submitLabel={t.createHackathon}
          submittingLabel={t.creating}
          onSubmit={handleSubmit}
          onCancel={() => navigate('/hackathons')}
        >
          <section className="registration-questions" aria-labelledby="create-questions-heading">
            <h2 id="create-questions-heading">Pytania rejestracyjne</h2>
            {questions.map((question, index) => (
              <fieldset className="question-editor" key={question.localId}>
                <label htmlFor={`create-question-${question.localId}`}>
                  Pytanie {index + 1}
                </label>
                <input
                  id={`create-question-${question.localId}`}
                  value={question.content}
                  maxLength={500}
                  onChange={(event) =>
                    setQuestions((current) =>
                      current.map((item) =>
                        item.localId === question.localId
                          ? { ...item, content: event.target.value }
                          : item,
                      ),
                    )
                  }
                />
                <label>
                  <input
                    type="checkbox"
                    checked={question.is_required}
                    onChange={(event) =>
                      setQuestions((current) =>
                        current.map((item) =>
                          item.localId === question.localId
                            ? { ...item, is_required: event.target.checked }
                            : item,
                        ),
                      )
                    }
                  />{' '}
                  Wymagane
                </label>
                {questions.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    aria-label={`Usuń pytanie ${index + 1}`}
                    onClick={() =>
                      setQuestions((current) =>
                        current.filter((item) => item.localId !== question.localId),
                      )
                    }
                  >
                    Usuń
                  </Button>
                )}
              </fieldset>
            ))}
            <Button
              type="button"
              variant="ghost"
              disabled={questions.length >= 50}
              onClick={() => setQuestions((current) => [...current, createQuestion()])}
            >
              Dodaj pytanie
            </Button>
            {questions.length >= 50 && (
              <p role="status">Możesz dodać maksymalnie 50 pytań.</p>
            )}
          </section>
        </HackathonForm>
      </Card>
    </main>
  )
}
