import { useEffect, useState } from 'react'
import { Alert, Spinner } from '../../../components/ui'
import {
  createRegistrationQuestion,
  deleteRegistrationQuestion,
  getRegistrationQuestions,
} from '../api/registrationApi'
import type {
  RegistrationQuestion,
  RegistrationQuestionPayload,
} from '../types'
import {
  areRegistrationQuestionsLocked,
  getQuestionManagementErrorMessage,
  getQuestionsErrorMessage,
} from '../utils/registrationMessages'
import { RegistrationQuestionForm } from './RegistrationQuestionForm'
import { RegistrationQuestionList } from './RegistrationQuestionList'

interface RegistrationQuestionsEditorProps {
  hackathonPublicId: string
}

export function RegistrationQuestionsEditor({
  hackathonPublicId,
}: RegistrationQuestionsEditorProps) {
  const [questions, setQuestions] = useState<RegistrationQuestion[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [isAdding, setIsAdding] = useState(false)
  const [isLocked, setIsLocked] = useState(false)
  const [deletingQuestionId, setDeletingQuestionId] = useState<string | null>(null)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [mutationError, setMutationError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadQuestions() {
      setIsLoading(true)
      setLoadError(null)

      try {
        setQuestions(
          await getRegistrationQuestions(hackathonPublicId, controller.signal),
        )
      } catch (error) {
        if (!controller.signal.aborted) {
          setLoadError(getQuestionsErrorMessage(error))
        }
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadQuestions()
    return () => controller.abort()
  }, [hackathonPublicId])

  function handleMutationError(error: unknown) {
    setMutationError(getQuestionManagementErrorMessage(error))
    if (areRegistrationQuestionsLocked(error)) setIsLocked(true)
  }

  async function handleAdd(payload: RegistrationQuestionPayload): Promise<boolean> {
    setIsAdding(true)
    setMutationError(null)

    try {
      const question = await createRegistrationQuestion(hackathonPublicId, payload)
      setQuestions((currentQuestions) => [...currentQuestions, question])
      return true
    } catch (error) {
      handleMutationError(error)
      return false
    } finally {
      setIsAdding(false)
    }
  }

  async function handleDelete(questionPublicId: string) {
    setDeletingQuestionId(questionPublicId)
    setMutationError(null)

    try {
      await deleteRegistrationQuestion(hackathonPublicId, questionPublicId)
      setQuestions((currentQuestions) =>
        currentQuestions.filter((question) => question.public_id !== questionPublicId),
      )
    } catch (error) {
      handleMutationError(error)
    } finally {
      setDeletingQuestionId(null)
    }
  }

  if (isLoading) return <Spinner label="Ładowanie pytań…" />
  if (loadError) return <Alert variant="error">{loadError}</Alert>

  return (
    <section className="registration-questions-editor" aria-label="Pytania rejestracyjne">
      {mutationError && <Alert variant="error">{mutationError}</Alert>}
      <RegistrationQuestionForm
        disabled={isLocked}
        isSubmitting={isAdding}
        onAdd={handleAdd}
      />
      <RegistrationQuestionList
        disabled={isLocked}
        questions={questions}
        deletingQuestionId={deletingQuestionId}
        onDelete={(questionPublicId) => void handleDelete(questionPublicId)}
      />
    </section>
  )
}
