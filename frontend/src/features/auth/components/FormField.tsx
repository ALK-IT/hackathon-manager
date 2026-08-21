import type { InputHTMLAttributes } from 'react'

interface FormFieldProps extends InputHTMLAttributes<HTMLInputElement> {
  label: string
  error?: string
}

export function FormField({ label, error, id, ...inputProps }: FormFieldProps) {
  const errorId = `${id}-error`

  return (
    <div className="form-field">
      <label htmlFor={id}>{label}</label>
      <input
        {...inputProps}
        id={id}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? errorId : undefined}
      />
      {error && (
        <span id={errorId} className="field-error">
          {error}
        </span>
      )}
    </div>
  )
}
