import { useEffect, useState, type FormEvent } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import {
  createRegistration,
  getMyRegistration,
  getRegistrationQuestions,
} from '../api/registrationApi'
import type {
  RegistrationQuestion,
  RegistrationResponse,
  TeamMode,
  TeamSelection,
} from '../types'
import {
  getQuestionsErrorMessage,
  getRegistrationErrorMessage,
  isRegistrationNotFoundError,
} from '../utils/registrationMessages'
import {
  hasRegistrationFormErrors,
  validateRegistrationForm,
  type RegistrationFormErrors,
} from '../utils/validation'

const emptyErrors: RegistrationFormErrors = { answers: {} }
const registrationStatusLabels: Record<RegistrationResponse['status'], string> = {
  pending: 'oczekujące',
  accepted: 'zaakceptowane',
  rejected: 'odrzucone',
}

export function RegistrationEntryPage() {
  const navigate = useNavigate()
  const { hackathonPublicId } = useParams()
  const [questions, setQuestions] = useState<RegistrationQuestion[]>([])
  const [answers, setAnswers] = useState<Record<string, string>>({})
  const [teamMode, setTeamMode] = useState<TeamMode>('none')
  const [teamName, setTeamName] = useState('')
  const [joinCode, setJoinCode] = useState('')
  const [errors, setErrors] = useState<RegistrationFormErrors>(emptyErrors)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [registration, setRegistration] = useState<RegistrationResponse | null>(null)
  const [isExistingRegistration, setIsExistingRegistration] = useState(false)

  useEffect(() => {
    const controller = new AbortController()

    async function loadRegistrationEntry() {
      if (!hackathonPublicId) {
        setLoadError('Nieprawidłowy adres hackathonu.')
        setIsLoading(false)
        return
      }

      let shouldLoadQuestions = false

      try {
        const existingRegistration = await getMyRegistration(
          hackathonPublicId,
          controller.signal,
        )
        setRegistration(existingRegistration)
        setIsExistingRegistration(true)
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
        if (isRegistrationNotFoundError(error)) {
          shouldLoadQuestions = true
        } else {
          setLoadError('Nie udało się sprawdzić Twojego zgłoszenia. Spróbuj ponownie.')
        }
      }

      if (shouldLoadQuestions) {
        try {
          setQuestions(await getRegistrationQuestions(hackathonPublicId, controller.signal))
        } catch (error) {
          if (error instanceof Error && error.name === 'AbortError') return
          setLoadError(getQuestionsErrorMessage(error))
        }
      }

      if (!controller.signal.aborted) setIsLoading(false)
    }

    void loadRegistrationEntry()
    return () => controller.abort()
  }, [hackathonPublicId])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!hackathonPublicId) return

    const validationErrors = validateRegistrationForm({
      questions,
      answers,
      teamMode,
      teamName,
      joinCode,
    })
    setErrors(validationErrors)
    if (hasRegistrationFormErrors(validationErrors)) return

    let team: TeamSelection | null = null
    if (teamMode === 'create') {
      team = { action: 'create', name: teamName.trim() }
    } else if (teamMode === 'join') {
      team = { action: 'join', join_code: joinCode.trim().toUpperCase() }
    }

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      const result = await createRegistration(hackathonPublicId, {
        answers: questions.flatMap((question) => {
          const content = answers[question.public_id]?.trim()
          return content
            ? [{ question_public_id: question.public_id, content }]
            : []
        }),
        team,
      })
      setRegistration(result)
      setIsExistingRegistration(false)
    } catch (error) {
      setSubmitError(getRegistrationErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="app-page">
      <Card className="registration-entry-card">
        <h1>Rejestracja na hackathon</h1>

        {isLoading && <Spinner label="Ładowanie formularza…" />}
        {loadError && <Alert variant="error">{loadError}</Alert>}

        {registration && (
          <div className="state-stack">
            <Alert>
              {isExistingRegistration
                ? 'Masz już zgłoszenie do tego hackathonu.'
                : 'Zgłoszenie zostało wysłane.'}{' '}
              Status: {registrationStatusLabels[registration.status]}.
            </Alert>
            {registration.team && (
              <div>
                <p>Drużyna: {registration.team.name}</p>
                <p>
                  Kod dołączenia: <strong>{registration.team.join_code}</strong>
                </p>
              </div>
            )}
            {registration.status === 'accepted' && (
              <Button
                type="button"
                variant="ghost"
                onClick={() =>
                  navigate(`/hackathons/${hackathonPublicId}/participant-area`)
                }
              >
                Wejdź do hackathonu
              </Button>
            )}
            <Button type="button" variant="ghost" onClick={() => navigate('/hackathons')}>
              Wróć do listy
            </Button>
          </div>
        )}

        {!isLoading && !loadError && !registration && (
          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <section className="registration-questions" aria-labelledby="questions-heading">
              <h2 id="questions-heading">Pytania</h2>
              {questions.length === 0 && (
                <p>Ten hackathon nie zawiera dodatkowych pytań.</p>
              )}
              {questions.map((question) => {
                const fieldId = `question-${question.public_id}`
                const error = errors.answers[question.public_id]
                const errorId = `${fieldId}-error`
                return (
                  <div className="form-field" key={question.public_id}>
                    <label htmlFor={fieldId}>
                      {question.content}
                      {!question.is_required && ' (opcjonalne)'}
                    </label>
                    <textarea
                      id={fieldId}
                      rows={4}
                      maxLength={5000}
                      required={question.is_required}
                      value={answers[question.public_id] ?? ''}
                      aria-invalid={Boolean(error)}
                      aria-describedby={error ? errorId : undefined}
                      onChange={(event) =>
                        setAnswers((current) => ({
                          ...current,
                          [question.public_id]: event.target.value,
                        }))
                      }
                    />
                    {error && (
                      <span id={errorId} className="field-error">
                        {error}
                      </span>
                    )}
                  </div>
                )
              })}
            </section>

            <fieldset className="team-options">
              <legend>Drużyna</legend>
              <label>
                <input
                  type="radio"
                  name="team-mode"
                  value="none"
                  checked={teamMode === 'none'}
                  onChange={() => setTeamMode('none')}
                />
                Bez drużyny
              </label>
              <label>
                <input
                  type="radio"
                  name="team-mode"
                  value="create"
                  checked={teamMode === 'create'}
                  onChange={() => setTeamMode('create')}
                />
                Utwórz drużynę
              </label>
              <label>
                <input
                  type="radio"
                  name="team-mode"
                  value="join"
                  checked={teamMode === 'join'}
                  onChange={() => setTeamMode('join')}
                />
                Dołącz kodem
              </label>
            </fieldset>

            {teamMode === 'create' && (
              <FormField
                id="team-name"
                label="Nazwa drużyny"
                value={teamName}
                error={errors.teamName}
                maxLength={200}
                required
                onChange={(event) => setTeamName(event.target.value)}
              />
            )}

            {teamMode === 'join' && (
              <FormField
                id="team-join-code"
                label="Kod drużyny"
                value={joinCode}
                error={errors.joinCode}
                minLength={8}
                maxLength={8}
                required
                onChange={(event) => setJoinCode(event.target.value.toUpperCase())}
              />
            )}

            {submitError && <Alert variant="error">{submitError}</Alert>}

            <div className="form-actions">
              <Button type="submit" disabled={isSubmitting}>
                {isSubmitting ? 'Wysyłanie…' : 'Wyślij zgłoszenie'}
              </Button>
              <Button type="button" variant="ghost" onClick={() => navigate('/hackathons')}>
                Anuluj
              </Button>
            </div>
          </form>
        )}
      </Card>
    </main>
  )
}
