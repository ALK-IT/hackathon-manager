import { Button } from '../../../components/ui'

interface RegistrationQuestionDraftProps {
  index: number
  content: string
  isRequired: boolean
  error?: string
  onContentChange: (content: string) => void
  onRequiredChange: (isRequired: boolean) => void
  onRemove: () => void
}

export function RegistrationQuestionDraft({
  index,
  content,
  isRequired,
  error,
  onContentChange,
  onRequiredChange,
  onRemove,
}: RegistrationQuestionDraftProps) {
  const fieldId = `registration-question-${index}`
  const errorId = `${fieldId}-error`

  return (
    <fieldset>
      <legend>Pytanie {index}</legend>
      <div className="form-field">
        <label htmlFor={fieldId}>Treść pytania</label>
        <textarea
          id={fieldId}
          rows={3}
          maxLength={500}
          required
          value={content}
          aria-invalid={Boolean(error)}
          aria-describedby={error ? errorId : undefined}
          onChange={(event) => onContentChange(event.target.value)}
        />
        {error && (
          <span id={errorId} className="field-error">
            {error}
          </span>
        )}
      </div>
      <label>
        <input
          type="checkbox"
          checked={isRequired}
          onChange={(event) => onRequiredChange(event.target.checked)}
        />
        Pytanie wymagane
      </label>
      <Button
        type="button"
        variant="ghost"
        aria-label={`Usuń pytanie ${index}`}
        onClick={onRemove}
      >
        −
      </Button>
    </fieldset>
  )
}
