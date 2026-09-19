import { useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Alert, Button } from '../../../components/ui'
import { useAuth } from '../hooks/useAuth'
import { getRegisterErrorMessage } from '../utils/authMessages'
import { validateRegister, type RegisterErrors } from '../utils/validation'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'
import { useTranslation } from '../../../i18n/useTranslation'

export function RegisterPage() {
  const { register } = useAuth()
  const { language, t } = useTranslation()
  const navigate = useNavigate()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [errors, setErrors] = useState<RegisterErrors>({})
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const validationErrors = validateRegister(name, email, password, confirmPassword, language)
    setErrors(validationErrors)
    if (Object.keys(validationErrors).length > 0) return

    setSubmitError(null)
    setIsSubmitting(true)
    try {
      await register({ name: name.trim(), email: email.trim().toLowerCase(), password })
      navigate('/login', { replace: true, state: { registered: true } })
    } catch (error) {
      setSubmitError(getRegisterErrorMessage(error, language))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <AuthPageLayout
      title={t.registrationTitle}
      footerText={t.haveAccount}
      footerLinkText={t.login}
      footerLinkTo="/login"
    >
      {submitError && <Alert variant="error">{submitError}</Alert>}
      <form className="auth-form" onSubmit={handleSubmit} noValidate>
        <FormField
          id="register-name"
          label={t.username}
          autoComplete="name"
          value={name}
          error={errors.name}
          onChange={(event) => setName(event.target.value)}
        />
        <FormField
          id="register-email"
          label={t.email}
          type="email"
          autoComplete="email"
          value={email}
          error={errors.email}
          onChange={(event) => setEmail(event.target.value)}
        />
        <FormField
          id="register-password"
          label={t.password}
          type="password"
          autoComplete="new-password"
          value={password}
          error={errors.password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <FormField
          id="register-confirm-password"
          label={t.confirmPassword}
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          error={errors.confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
        />
        <Button type="submit" disabled={isSubmitting}>
          {isSubmitting ? t.creatingAccount : t.createAccount}
        </Button>
      </form>
    </AuthPageLayout>
  )
}
