import { useState, type FormEvent } from 'react'
import { Alert, Button } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import { createIndividualResourcePool } from '../api/resourceManagementApi'
import { getResourceErrorMessage } from '../utils/resourceMessages'

interface ResourcePoolCreatorProps {
  hackathonPublicId: string
  onCreated: (resourcePublicId: string) => void | Promise<void>
}

export function ResourcePoolCreator({
  hackathonPublicId,
  onCreated,
}: ResourcePoolCreatorProps) {
  const [isOpen, setIsOpen] = useState(false)
  const [name, setName] = useState('')
  const [valuesText, setValuesText] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setError(null)

    const normalizedName = name.trim()
    const values = valuesText
      .split(/\r?\n/)
      .map((value) => value.trim())
      .filter(Boolean)

    if (!normalizedName) {
      setError('Podaj nazwę zasobu.')
      return
    }
    if (values.length === 0) {
      setError('Dodaj przynajmniej jeden klucz.')
      return
    }
    if (values.length > 100) {
      setError('Jednorazowo możesz dodać maksymalnie 100 kluczy.')
      return
    }
    if (new Set(values).size !== values.length) {
      setError('Każdy klucz w puli musi być unikalny.')
      return
    }
    if (values.some((value) => value.length > 4096)) {
      setError('Pojedynczy klucz nie może przekraczać 4096 znaków.')
      return
    }

    setIsSubmitting(true)
    try {
      const resource = await createIndividualResourcePool(
        hackathonPublicId,
        normalizedName,
        values,
      )
      setName('')
      setValuesText('')
      setIsOpen(false)
      await onCreated(resource.public_id)
    } catch (requestError) {
      setError(
        getResourceErrorMessage(
          requestError,
          'Nie udało się utworzyć puli zasobów.',
        ),
      )
    } finally {
      setIsSubmitting(false)
    }
  }

  if (!isOpen) {
    return (
      <Button type="button" variant="ghost" onClick={() => setIsOpen(true)}>
        Utwórz zasób
      </Button>
    )
  }

  return (
    <form
      className="attendance-resource-create-form"
      onSubmit={handleSubmit}
      noValidate
    >
      <FormField
        id="resource-name"
        label="Nazwa zasobu"
        value={name}
        maxLength={200}
        required
        onChange={(event) => setName(event.target.value)}
      />
      <div className="form-field">
        <label htmlFor="resource-values">Klucze — jeden w wierszu</label>
        <textarea
          id="resource-values"
          value={valuesText}
          rows={6}
          required
          autoComplete="off"
          spellCheck={false}
          onChange={(event) => setValuesText(event.target.value)}
        />
      </div>
      {error && <Alert variant="error">{error}</Alert>}
      <div className="attendance-resource-create-actions">
        <Button type="submit" variant="ghost" disabled={isSubmitting}>
          {isSubmitting ? 'Tworzenie…' : 'Utwórz i dodaj klucze'}
        </Button>
        <Button
          type="button"
          variant="ghost"
          disabled={isSubmitting}
          onClick={() => {
            setError(null)
            setIsOpen(false)
          }}
        >
          Anuluj
        </Button>
      </div>
    </form>
  )
}
