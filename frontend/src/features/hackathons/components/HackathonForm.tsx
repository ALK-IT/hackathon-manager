import { useState, type FormEvent } from 'react'
import { Button } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import {
  validateHackathon,
  type HackathonFormErrors,
  type HackathonFormValues,
} from '../utils/validation'

export interface NormalizedHackathonValues {
  name: string
  description: string
  start_date: string
  end_date: string
  registration_opens_at: string
  registration_deadline: string | null
  capacity: number | null
  max_team_size: number
}

interface HackathonFormProps {
  initialValues: HackathonFormValues
  isSubmitting: boolean
  submitLabel: string
  submittingLabel: string
  registrationDeadlineRequired?: boolean
  onSubmit: (values: NormalizedHackathonValues) => void | Promise<void>
  onCancel: () => void
}

function toLocalDateTime(date: Date): string {
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

export function HackathonForm({
  initialValues,
  isSubmitting,
  submitLabel,
  submittingLabel,
  registrationDeadlineRequired = false,
  onSubmit,
  onCancel,
}: HackathonFormProps) {
  const [values, setValues] = useState(initialValues)
  const [errors, setErrors] = useState<HackathonFormErrors>({})

  function updateValue(name: keyof HackathonFormValues, value: string) {
    setValues((current) => ({ ...current, [name]: value }))
  }

  function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const validationErrors = validateHackathon(values, { registrationDeadlineRequired })
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    void onSubmit({
      name: values.name.trim(),
      description: values.description.trim(),
      start_date: new Date(values.startDate).toISOString(),
      end_date: new Date(values.endDate).toISOString(),
      registration_opens_at: new Date(values.registrationOpensAt).toISOString(),
      registration_deadline: values.registrationDeadline
        ? new Date(values.registrationDeadline).toISOString()
        : null,
      capacity: values.capacity ? Number(values.capacity) : null,
      max_team_size: Number(values.maxTeamSize),
    })
  }

  return (
    <form className="auth-form" onSubmit={handleSubmit} noValidate>
      <FormField
        id="hackathon-name"
        label="Nazwa"
        value={values.name}
        error={errors.name}
        maxLength={200}
        required
        onChange={(event) => updateValue('name', event.target.value)}
      />
      <FormField
        id="hackathon-description"
        label="Opis"
        value={values.description}
        error={errors.description}
        maxLength={5000}
        onChange={(event) => updateValue('description', event.target.value)}
      />
      <FormField
        id="hackathon-start-date"
        label="Rozpoczęcie hackathonu"
        type="datetime-local"
        value={values.startDate}
        error={errors.startDate}
        required
        onChange={(event) => updateValue('startDate', event.target.value)}
      />
      <FormField
        id="hackathon-end-date"
        label="Zakończenie hackathonu"
        type="datetime-local"
        value={values.endDate}
        error={errors.endDate}
        required
        onChange={(event) => updateValue('endDate', event.target.value)}
      />
      <div className="registration-opening-field">
        <FormField
          id="registration-opens-at"
          label="Otwarcie zapisów"
          type="datetime-local"
          value={values.registrationOpensAt}
          error={errors.registrationOpensAt}
          required
          onChange={(event) => updateValue('registrationOpensAt', event.target.value)}
        />
        <Button
          type="button"
          variant="ghost"
          onClick={() => updateValue('registrationOpensAt', toLocalDateTime(new Date()))}
        >
          Teraz
        </Button>
      </div>
      <FormField
        id="registration-deadline"
        label={
          registrationDeadlineRequired
            ? 'Zamknięcie zapisów'
            : 'Zamknięcie zapisów (opcjonalne)'
        }
        type="datetime-local"
        value={values.registrationDeadline}
        error={errors.registrationDeadline}
        required={registrationDeadlineRequired}
        onChange={(event) => updateValue('registrationDeadline', event.target.value)}
      />
      <FormField
        id="hackathon-capacity"
        label="Limit uczestników (opcjonalny)"
        type="number"
        min="1"
        value={values.capacity}
        error={errors.capacity}
        onChange={(event) => updateValue('capacity', event.target.value)}
      />
      <FormField
        id="hackathon-max-team-size"
        label="Maksymalna wielkość drużyny"
        type="number"
        min="1"
        value={values.maxTeamSize}
        error={errors.maxTeamSize}
        required
        onChange={(event) => updateValue('maxTeamSize', event.target.value)}
      />
      <div className="form-actions">
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? submittingLabel : submitLabel}
        </Button>
        <Button type="button" variant="ghost" onClick={onCancel}>
          Anuluj
        </Button>
      </div>
    </form>
  )
}
