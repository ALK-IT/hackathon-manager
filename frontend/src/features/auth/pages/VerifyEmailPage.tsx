import { useEffect, useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert, Button, Spinner } from '../../../components/ui'
import { resendVerificationRequest, verifyEmailRequest } from '../api/authApi'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'
import { isValidEmail } from '../utils/validation'
import { useTranslation } from '../../../i18n/useTranslation'

export function VerifyEmailPage() {
  const { language, t } = useTranslation()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>(
    token ? 'loading' : 'error',
  )
  const [email, setEmail] = useState('')
  const [resendMessage, setResendMessage] = useState<string | null>(null)
  const [resending, setResending] = useState(false)

  useEffect(() => {
    if (!token) return
    let active = true
    verifyEmailRequest(token)
      .then(() => {
        if (active) setStatus('success')
      })
      .catch(() => {
        if (active) setStatus('error')
      })
    return () => {
      active = false
    }
  }, [token])

  async function resend(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isValidEmail(email)) {
      setResendMessage(t.invalidEmail)
      return
    }
    setResending(true)
    try {
      await resendVerificationRequest(email.trim().toLowerCase())
      setResendMessage(language === 'en' ? 'If the account exists, we sent a new activation link.' : 'Jeśli konto istnieje, wysłaliśmy nowy link aktywacyjny.')
    } catch {
      setResendMessage(language === 'en' ? 'Could not send the message. Try again.' : 'Nie udało się wysłać wiadomości. Spróbuj ponownie.')
    } finally {
      setResending(false)
    }
  }

  return (
    <AuthPageLayout
      title={t.verifyAccount}
      footerText={t.verifiedAccountQuestion}
      footerLinkText={t.login}
      footerLinkTo="/login"
    >
      {status === 'loading' && <Spinner label={t.verifyingAccount} />}
      {status === 'success' && (
        <Alert>
          {t.accountVerified} <Link to="/login">{t.goToLogin}</Link>.
        </Alert>
      )}
      {status === 'error' && (
        <>
          {token && (
            <Alert variant="error">{language === 'en' ? 'The link is invalid, expired, or has already been used.' : 'Link jest nieprawidłowy, wygasł albo został już użyty.'}</Alert>
          )}
          {resendMessage && <Alert>{resendMessage}</Alert>}
          <form className="auth-form" onSubmit={resend} noValidate>
            <FormField
              id="verification-email"
              label={t.email}
              type="email"
              autoComplete="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
            />
            <Button type="submit" disabled={resending}>
              {resending ? t.sending : t.sendNewLink}
            </Button>
          </form>
        </>
      )}
    </AuthPageLayout>
  )
}
