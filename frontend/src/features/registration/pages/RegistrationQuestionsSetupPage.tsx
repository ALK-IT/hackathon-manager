import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card } from '../../../components/ui'
import { createRegistrationQuestions } from '../api/registrationApi'
import type { RegistrationQuestionPayload } from '../types'
import { getSaveQuestionsErrorMessage } from '../utils/registrationMessages'

const MAX_QUESTIONS = 50

interface EditableQuestion extends RegistrationQuestionPayload {
  localId: string
}

function createEditableQuestion(): EditableQuestion {
  return { localId: crypto.randomUUID(), content: '', is_required: true }
}

export function RegistrationQuestionsSetupPage() {
  const { hackathonPublicId } = useParams()
  const navigate = useNavigate()
  const [questions, setQuestions] = useState<EditableQuestion[]>(() => [createEditableQuestion()])
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateQuestion(localId: string, patch: Partial<RegistrationQuestionPayload>) {
    setQuestions((current) =>
      current.map((question) =>
        question.localId === localId ? { ...question, ...patch } : question,
      ),
    )
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const normalized = questions.map((question) => ({
      content: question.content.trim(),
      is_required: question.is_required,
    }))
    if (!hackathonPublicId || normalized.some((question) => !question.content)) {
      setError('Uzupełnij treść każdego pytania.')
      return
    }

    setError(null)
    setIsSubmitting(true)
    try {
      await createRegistrationQuestions(hackathonPublicId, normalized)
      navigate(`/hackathons/${hackathonPublicId}`, { replace: true })
    } catch (requestError) {
      setError(getSaveQuestionsErrorMessage(requestError))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <Card className="create-hackathon-card">
        <h1>Pytania rejestracyjne</h1>
        {error && <Alert variant="error">{error}</Alert>}
        <form className="auth-form" onSubmit={handleSubmit}>
          {questions.map((question, index) => (
            <fieldset className="question-editor" key={question.localId}>
              <label htmlFor={`question-${index}`}>Pytanie {index + 1}</label>
              <input
                id={`question-${index}`}
                value={question.content}
                maxLength={500}
                onChange={(event) =>
                  updateQuestion(question.localId, { content: event.target.value })
                }
              />
              <label>
                <input
                  type="checkbox"
                  checked={question.is_required}
                  onChange={(event) =>
                    updateQuestion(question.localId, { is_required: event.target.checked })
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
            disabled={questions.length >= MAX_QUESTIONS}
            onClick={() => setQuestions((current) => [...current, createEditableQuestion()])}
          >
            Dodaj pytanie
          </Button>
          {questions.length >= MAX_QUESTIONS && (
            <p role="status">Możesz dodać maksymalnie 50 pytań.</p>
          )}
          <div className="form-actions">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Zapisywanie…' : 'Zapisz pytania'}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate(`/hackathons/${hackathonPublicId}`)}
            >
              Pomiń
            </Button>
          </div>
        </form>
      </Card>
    </main>
  )
}
