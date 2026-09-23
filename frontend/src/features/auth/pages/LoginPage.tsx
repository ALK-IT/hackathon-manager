import { useState, type FormEvent } from 'react'
import { Link, useLocation, useNavigate } from 'react-router-dom'
import { Alert, Button } from '../../../components/ui'
import { ApiError } from '../../../lib/api/client'
import { useAuth } from '../hooks/useAuth'
import { getLoginErrorMessage } from '../utils/authMessages'
import { validateLogin, type LoginErrors } from '../utils/validation'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'
import { useTranslation } from '../../../i18n/useTranslation'

export function LoginPage() {
  const { login } = useAuth()
  const { language, t } = useTranslation()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<LoginErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [showResendLink, setShowResendLink] = useState(false)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const validationErrors = validateLogin(email, password, language)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitError(null)
    setShowResendLink(false)
    setIsSubmitting(true)
    try {
      await login(email.trim().toLowerCase(), password)
      const destination = (location.state as { from?: string } | null)?.from ?? '/hackathons'
      navigate(destination, { replace: true })
    } catch (error) {
      setSubmitError(getLoginErrorMessage(error, language))
      setShowResendLink(error instanceof ApiError && error.status === 403)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthPageLayout
      title={t.signInTitle}
      footerText={t.noAccount}
      footerLinkText={t.signUp}
      footerLinkTo="/register"
    >
      {(location.state as { registered?: boolean } | null)?.registered && (
        <Alert>{t.accountCreated}</Alert>
      )}
      {submitError && <Alert variant="error">{submitError}</Alert>}
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <FormField
          id="login-email"
          label={t.email}
          type="email"
          autoComplete="email"
          value={email}
          error={errors.email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <FormField
          id="login-password"
          label={t.password}
          type="password"
          autoComplete="current-password"
          value={password}
          error={errors.password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? t.signingIn : t.login}
        </Button>
        <Link to="/forgot-password">{t.forgotPassword}</Link>
        {showResendLink && (
          <Link to="/verify-email">{t.resendActivation}</Link>
        )}
      </form>
    </AuthPageLayout>
  )
}
