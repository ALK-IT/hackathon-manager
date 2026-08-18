import { Button } from '../../../components/ui'
import type { RegistrationQuestion } from '../types'

interface RegistrationQuestionListProps {
  disabled: boolean
  questions: RegistrationQuestion[]
  deletingQuestionId: string | null
  onDelete: (questionPublicId: string) => void
}

export function RegistrationQuestionList({
  disabled,
  questions,
  deletingQuestionId,
  onDelete,
}: RegistrationQuestionListProps) {
  if (questions.length === 0) {
    return (
      <p className="registration-questions-empty">
        Nie dodano jeszcze pytań. Ten krok możesz pominąć.
      </p>
    )
  }

  return (
    <ul className="registration-question-list" aria-label="Dodane pytania">
      {questions.map((question) => {
        const isDeleting = deletingQuestionId === question.public_id

        return (
          <li className="registration-question-item" key={question.public_id}>
            <div className="registration-question-content">
              <span>{question.content}</span>
              <span className="registration-question-kind">
                {question.is_required ? 'Wymagane' : 'Opcjonalne'}
              </span>
            </div>
            <Button
              type="button"
              variant="danger"
              disabled={disabled || deletingQuestionId !== null}
              aria-label={`Usuń pytanie: ${question.content}`}
              onClick={() => onDelete(question.public_id)}
            >
              {isDeleting ? 'Usuwanie…' : 'Usuń'}
            </Button>
          </li>
        )
      })}
    </ul>
  )
}
