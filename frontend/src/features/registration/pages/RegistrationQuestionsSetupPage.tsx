import { useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card } from '../../../components/ui'
import { createRegistrationQuestions } from '../api/registrationApi'
import type { RegistrationQuestionPayload } from '../types'

export function RegistrationQuestionsSetupPage() {
  const { hackathonPublicId } = useParams()
  const navigate = useNavigate()
  const [questions, setQuestions] = useState<RegistrationQuestionPayload[]>([
    { content: '', is_required: true },
  ])
  const [error, setError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  function updateQuestion(index: number, patch: Partial<RegistrationQuestionPayload>) {
    setQuestions((current) =>
      current.map((question, questionIndex) =>
        questionIndex === index ? { ...question, ...patch } : question,
      ),
    )
  }

  async function handleSubmit(event: FormEvent) {
    event.preventDefault()
    const normalized = questions.map((question) => ({
      ...question,
      content: question.content.trim(),
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
    } catch {
      setError('Nie udało się zapisać pytań. Spróbuj ponownie.')
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
            <fieldset className="question-editor" key={index}>
              <label htmlFor={`question-${index}`}>Pytanie {index + 1}</label>
              <input
                id={`question-${index}`}
                value={question.content}
                maxLength={500}
                onChange={(event) => updateQuestion(index, { content: event.target.value })}
              />
              <label>
                <input
                  type="checkbox"
                  checked={question.is_required}
                  onChange={(event) =>
                    updateQuestion(index, { is_required: event.target.checked })
                  }
                />{' '}
                Wymagane
              </label>
              {questions.length > 1 && (
                <Button
                  type="button"
                  variant="ghost"
                  onClick={() =>
                    setQuestions((current) => current.filter((_, itemIndex) => itemIndex !== index))
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
            onClick={() =>
              setQuestions((current) => [...current, { content: '', is_required: true }])
            }
          >
            Dodaj pytanie
          </Button>
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
