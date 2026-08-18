import { useState, type FormEvent } from 'react'
import { Button } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import type { RegistrationQuestionPayload } from '../types'

interface RegistrationQuestionFormProps {
  disabled: boolean
  isSubmitting: boolean
  onAdd: (payload: RegistrationQuestionPayload) => Promise<boolean>
}

export function RegistrationQuestionForm({
  disabled,
  isSubmitting,
  onAdd,
}: RegistrationQuestionFormProps) {
  const [content, setContent] = useState('')
  const [isRequired, setIsRequired] = useState(true)
  const [contentError, setContentError] = useState<string | undefined>()

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const normalizedContent = content.trim()

    if (!normalizedContent) {
      setContentError('Podaj treść pytania.')
      return
    }

    setContentError(undefined)
    const wasAdded = await onAdd({
      content: normalizedContent,
      is_required: isRequired,
    })
    if (!wasAdded) return

    setContent('')
    setIsRequired(true)
  }

  const controlsDisabled = disabled || isSubmitting

  return (
    <form className="registration-question-form" onSubmit={handleSubmit} noValidate>
      <FormField
        id="registration-question-content"
        label="Treść pytania"
        value={content}
        error={contentError}
        maxLength={500}
        required
        disabled={controlsDisabled}
        onChange={(event) => setContent(event.target.value)}
      />
      <label className="registration-question-required">
        <input
          type="checkbox"
          checked={isRequired}
          disabled={controlsDisabled}
          onChange={(event) => setIsRequired(event.target.checked)}
        />
        Wymagane
      </label>
      <Button type="submit" disabled={controlsDisabled}>
        {isSubmitting ? 'Dodawanie…' : '+ Dodaj pytanie'}
      </Button>
    </form>
  )
}
