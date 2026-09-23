import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert, Button } from '../../../components/ui'
import { resetPasswordRequest } from '../api/authApi'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'
import { useTranslation } from '../../../i18n/useTranslation'

export function ResetPasswordPage() {
  const { language, t } = useTranslation()
  const [searchParams] = useSearchParams()
  const token = searchParams.get('token')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [error, setError] = useState<string | null>(null)
  const [tokenRejected, setTokenRejected] = useState(false)
  const [saved, setSaved] = useState(false)
  const [submitting, setSubmitting] = useState(false)

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    if (!token) {
      setError(language === 'en' ? 'The password reset token is missing.' : 'Brakuje tokenu resetowania hasła.')
      return
    }
    if (password.length < 8) {
      setError(t.shortPassword)
      return
    }
    if (password !== confirmPassword) {
      setError(t.passwordsDiffer)
      return
    }
    setError(null)
    setTokenRejected(false)
    setSubmitting(true)
    try {
      await resetPasswordRequest(token, password, confirmPassword)
      setSaved(true)
    } catch {
      setError(language === 'en' ? 'The link is invalid, expired, or has already been used.' : 'Link jest nieprawidłowy, wygasł albo został już użyty.')
      setTokenRejected(true)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthPageLayout
      title={t.setNewPassword}
      footerText={t.passwordChangedQuestion}
      footerLinkText={t.login}
      footerLinkTo="/login"
    >
      {saved && <Alert>{t.passwordChanged}</Alert>}
      {error && <Alert variant="error">{error}</Alert>}
      {tokenRejected && <Link to="/forgot-password">{t.requestNewLink}</Link>}
      <form className="auth-form" onSubmit={submit} noValidate>
        <FormField
          id="reset-password"
          label={t.newPassword}
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <FormField
          id="reset-confirm-password"
          label={t.repeatNewPassword}
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
        />
        <Button type="submit" disabled={submitting || saved}>
          {submitting ? t.saving : t.changePassword}
        </Button>
      </form>
    </AuthPageLayout>
  )
}
