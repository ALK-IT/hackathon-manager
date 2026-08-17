import { useState, type FormEvent } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import { Alert, Button } from '../../../components/ui'
import { useAuth } from '../hooks/useAuth'
import { getLoginErrorMessage } from '../utils/authMessages'
import { validateLogin, type LoginErrors } from '../utils/validation'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'

export function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const location = useLocation()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [errors, setErrors] = useState<LoginErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const validationErrors = validateLogin(email, password)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      await login(email.trim().toLowerCase(), password)
      navigate('/', { replace: true })
    } catch (error) {
      setSubmitError(getLoginErrorMessage(error))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthPageLayout
      title="Logowanie"
      footerText="Nie masz konta?"
      footerLinkText="Zarejestruj się"
      footerLinkTo="/register"
    >
      {(location.state as { registered?: boolean } | null)?.registered && (
        <Alert>Konto zostało utworzone. Możesz się zalogować.</Alert>
      )}
      {submitError && <Alert variant="error">{submitError}</Alert>}
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <FormField
          id="login-email"
          label="E-mail"
          type="email"
          autoComplete="email"
          value={email}
          error={errors.email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <FormField
          id="login-password"
          label="Hasło"
          type="password"
          autoComplete="current-password"
          value={password}
          error={errors.password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? 'Logowanie…' : 'Zaloguj się'}
        </Button>
      </form>
    </AuthPageLayout>
  )
}
