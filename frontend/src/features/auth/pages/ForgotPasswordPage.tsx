import { useState, type FormEvent } from 'react'
import { Alert, Button } from '../../../components/ui'
import { forgotPasswordRequest } from '../api/authApi'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'
import { isValidEmail } from '../utils/validation'

export function ForgotPasswordPage() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | undefined>()
  const [sent, setSent] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isValidEmail(email)) {
      setError('Podaj poprawny adres e-mail.')
      return
    }
    setError(undefined)
    setSubmitting(true)
    try {
      await forgotPasswordRequest(email.trim().toLowerCase())
      setSent(true)
    } catch {
      setError('Nie udało się wysłać wiadomości. Spróbuj ponownie.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthPageLayout
      title="Reset hasła"
      footerText="Pamiętasz hasło?"
      footerLinkText="Zaloguj się"
      footerLinkTo="/login"
    >
      {sent && <Alert>Jeśli konto istnieje, wysłaliśmy link do zmiany hasła.</Alert>}
      <form className="auth-form" onSubmit={submit} noValidate>
        <FormField
          id="forgot-password-email"
          label="E-mail"
          type="email"
          autoComplete="email"
          value={email}
          error={error}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Button type="submit" disabled={submitting || sent}>
          {submitting ? 'Wysyłanie…' : 'Wyślij link'}
        </Button>
      </form>
    </AuthPageLayout>
  )
}
