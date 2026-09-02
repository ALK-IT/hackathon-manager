import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert, Button, Spinner } from '../../../components/ui'
import { resendVerificationRequest, verifyEmailRequest } from '../api/authApi'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'
import { isValidEmail } from '../utils/validation'

export function VerifyEmailPage() {
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [status, setStatus] = useState<'ready' | 'loading' | 'success' | 'error'>(
    token ? 'ready' : 'error',
  )
  const [email, setEmail] = useState('')
  const [resendMessage, setResendMessage] = useState<string | null>(null)
  const [resending, setResending] = useState(false)

  async function verify() {
    if (!token) return
    setStatus('loading')
    try {
      await verifyEmailRequest(token)
      setStatus('success')
    } catch {
      setStatus('error')
    }
  }

  async function resend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isValidEmail(email)) {
      setResendMessage('Podaj poprawny adres e-mail.')
      return
    }
    setResending(true)
    try {
      await resendVerificationRequest(email.trim().toLowerCase())
      setResendMessage('Jeśli konto istnieje, wysłaliśmy nowy link aktywacyjny.')
    } catch {
      setResendMessage('Nie udało się wysłać wiadomości. Spróbuj ponownie.')
    } finally {
      setResending(false)
    }
  }

  return (
    <AuthPageLayout
      title="Potwierdzenie konta"
      footerText="Masz już potwierdzone konto?"
      footerLinkText="Zaloguj się"
      footerLinkTo="/login"
    >
      {status === 'loading' && <Spinner label="Potwierdzanie konta…" />}
      {status === 'ready' && (
        <>
          <Alert>Otworzyłeś link aktywacyjny. Potwierdź, że chcesz aktywować konto.</Alert>
          <Button type="button" onClick={verify}>
            Potwierdź konto
          </Button>
        </>
      )}
      {status === 'success' && (
        <Alert>
          Konto zostało potwierdzone. <Link to="/login">Przejdź do logowania</Link>.
        </Alert>
      )}
      {status === 'error' && (
        <>
          {token && (
            <Alert variant="error">Link jest nieprawidłowy, wygasł albo został już użyty.</Alert>
          )}
          {resendMessage && <Alert>{resendMessage}</Alert>}
          <form className="auth-form" onSubmit={resend} noValidate>
            <FormField
              id="verification-email"
              label="E-mail"
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <Button type="submit" disabled={resending}>
              {resending ? 'Wysyłanie…' : 'Wyślij nowy link'}
            </Button>
          </form>
        </>
      )}
    </AuthPageLayout>
  )
}
