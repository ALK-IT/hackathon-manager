import { useState, type FormEvent } from 'react'
import { Alert, Button } from '../../../components/ui'
import { forgotPasswordRequest } from '../api/authApi'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'
import { isValidEmail } from '../utils/validation'
import { useTranslation } from '../../../i18n/useTranslation'

export function ForgotPasswordPage() {
  const { t } = useTranslation()
  const [email, setEmail] = useState('')
  const [error, setError] = useState<string | undefined>()
  const [sent, setSent] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!isValidEmail(email)) {
      setError(t.invalidEmail)
      return
    }
    setError(undefined)
    setSubmitting(true)
    try {
      await forgotPasswordRequest(email.trim().toLowerCase())
      setSent(true)
    } catch {
      setError(t.passwordLinkError)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthPageLayout
      title={t.resetPassword}
      footerText={t.rememberPassword}
      footerLinkText={t.login}
      footerLinkTo="/login"
    >
      {sent && <Alert>{t.genericEmailSent}</Alert>}
      <form className="auth-form" onSubmit={submit} noValidate>
        <FormField
          id="forgot-password-email"
          label={t.email}
          type="email"
          autoComplete="email"
          value={email}
          error={error}
          onChange={(event) => setEmail(event.target.value)}
        />
        <Button type="submit" disabled={submitting || sent}>
          {submitting ? t.sending : t.sendLink}
        </Button>
      </form>
    </AuthPageLayout>
  )
}
