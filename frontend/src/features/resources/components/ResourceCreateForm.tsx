import { FormEvent, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { createResource, importResourceItems } from '../api/resourcesApi'
import { getResourcesErrorMessage } from '../utils/resourceMessages'

interface ResourceCreateFormProps {
  hackathonPublicId: string
  onCreated?: () => void
}

export function ResourceCreateForm({ hackathonPublicId, onCreated }: ResourceCreateFormProps) {
  const [name, setName] = useState('')
  const [target, setTarget] = useState<'individual' | 'team'>('individual')
  const [values, setValues] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [success, setSuccess] = useState<string | null>(null)
  const [isSaving, setIsSaving] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const items = values.split(/\r?\n/).map((value) => value.trim()).filter(Boolean)
    if (!name.trim() || items.length === 0) {
      setError('Podaj nazwę zasobu oraz co najmniej jedną wartość (po jednej wierszu).')
      return
    }
    setError(null)
    setSuccess(null)
    setIsSaving(true)
    try {
      const resource = await createResource(hackathonPublicId, { name: name.trim(), target })
      await importResourceItems(hackathonPublicId, resource.public_id, items)
      setName('')
      setValues('')
      setSuccess(`Zasób „${name.trim()}” został zapisany. Możesz teraz przypisać jego wartości uczestnikom.`)
      onCreated?.()
    } catch (requestError) {
      setError(getResourcesErrorMessage(requestError))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} aria-labelledby="resource-create-heading">
      <h3 id="resource-create-heading">Dodaj zasoby</h3>
      <p>Wartości zostaną zaimportowane do ręcznego przypisywania uczestnikom.</p>
      {error && <Alert variant="error">{error}</Alert>}
      {success && <Alert>{success}</Alert>}
      <label>
        Nazwa zasobu
        <input value={name} onChange={(event) => setName(event.target.value)} placeholder="np. Klucze API" />
      </label>
      <label>
        Przeznaczenie
        <select value={target} onChange={(event) => setTarget(event.target.value as 'individual' | 'team')}>
          <option value="individual">Uczestnik</option>
          <option value="team">Drużyna</option>
        </select>
      </label>
      <label>
        Wartości (jedna w wierszu)
        <textarea value={values} onChange={(event) => setValues(event.target.value)} rows={5} />
      </label>
      <Button type="submit" disabled={isSaving}>{isSaving ? 'Dodawanie…' : 'Zapisz zasób'}</Button>
    </form>
  )
}
