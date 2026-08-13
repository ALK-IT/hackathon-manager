import { useRef, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card } from '../../../components/ui'
import { createRegistrationQuestions } from '../api/registrationApi'
import { RegistrationQuestionDraft } from '../components/RegistrationQuestionDraft'
import { getCreateQuestionsErrorMessage } from '../utils/registrationMessages'

interface QuestionDraft {
  id: number
  content: string
  isRequired: boolean
}

function emptyQuestion(id: number): QuestionDraft {
  return { id, content: '', isRequired: true }
}

export function RegistrationQuestionsCreatePage() {
  const navigate = useNavigate()
  const { hackathonPublicId } = useParams()
  const nextQuestionId = useRef(2)
  const [questions, setQuestions] = useState<QuestionDraft[]>([emptyQuestion(1)])
  const [errors, setErrors] = useState<Record<number, string>>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  function addQuestion() {
    const id = nextQuestionId.current
    nextQuestionId.current += 1
    setQuestions((current) => [...current, emptyQuestion(id)])
  }

  function removeQuestion(id: number) {
    setQuestions((current) => current.filter((question) => question.id !== id))
    setErrors((current) => {
      const nextErrors = { ...current }
      delete nextErrors[id]
      return nextErrors
    })
  }

  function updateQuestion(id: number, changes: Partial<QuestionDraft>) {
    setQuestions((current) =>
      current.map((question) =>
        question.id === id ? { ...question, ...changes } : question,
      ),
    )
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!hackathonPublicId) {
      setSubmitError('Nieprawidłowy adres hackathonu.')
      return
    }

    const validationErrors: Record<number, string> = {}
    for (const question of questions) {
      const content = question.content.trim()
      if (!content) validationErrors[question.id] = 'Podaj treść pytania.'
      else if (content.length > 500) {
        validationErrors[question.id] = 'Pytanie może mieć maksymalnie 500 znaków.'
      }
    }
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    if (questions.length === 0) {
      navigate('/hackathons', { replace: true })
      return
    }

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      await createRegistrationQuestions(hackathonPublicId, {
        questions: questions.map((question) => ({
          content: question.content.trim(),
          is_required: question.isRequired,
        })),
      })
      navigate('/hackathons', { replace: true })
    } catch (error) {
      setSubmitError(getCreateQuestionsErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <Card className="create-hackathon-card">
        <h1>Dodaj pytania rekrutacyjne</h1>
        <p>Pytania zostaną zapisane razem po wysłaniu formularza.</p>
        {submitError && <Alert variant="error">{submitError}</Alert>}

        <form className="auth-form" onSubmit={handleSubmit} noValidate>
          {questions.map((question, index) => (
            <RegistrationQuestionDraft
              key={question.id}
              index={index + 1}
              content={question.content}
              isRequired={question.isRequired}
              error={errors[question.id]}
              onContentChange={(content) => updateQuestion(question.id, { content })}
              onRequiredChange={(isRequired) =>
                updateQuestion(question.id, { isRequired })
              }
              onRemove={() => removeQuestion(question.id)}
            />
          ))}

          <Button type="button" variant="ghost" onClick={addQuestion}>
            + Dodaj pytanie
          </Button>
          <div className="form-actions">
            <Button type="submit" disabled={isSubmitting}>
              {isSubmitting ? 'Zapisywanie…' : 'Zapisz pytania'}
            </Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate('/hackathons', { replace: true })}
            >
              Pomiń
            </Button>
          </div>
        </form>
      </Card>
    </main>
  )
}
