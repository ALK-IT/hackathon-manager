import { useState, type FormEvent } from 'react'
import { Link, useSearchParams } from 'react-router-dom'
import { Alert, Button } from '../../../components/ui'
import { resetPasswordRequest } from '../api/authApi'
import { AuthPageLayout } from '../components/AuthPageLayout'
import { FormField } from '../components/FormField'

export function ResetPasswordPage() {
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
      setError('Brakuje tokenu resetowania hasła.')
      return
    }
    if (password.length < 8) {
      setError('Hasło musi mieć co najmniej 8 znaków.')
      return
    }
    if (password !== confirmPassword) {
      setError('Hasła muszą być takie same.')
      return
    }
    setError(null)
    setTokenRejected(false)
    setSubmitting(true)
    try {
      await resetPasswordRequest(token, password, confirmPassword)
      setSaved(true)
    } catch {
      setError('Link jest nieprawidłowy, wygasł albo został już użyty.')
      setTokenRejected(true)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <AuthPageLayout
      title="Ustaw nowe hasło"
      footerText="Hasło zostało zmienione?"
      footerLinkText="Zaloguj się"
      footerLinkTo="/login"
    >
      {saved && <Alert>Hasło zostało zmienione. Możesz się zalogować.</Alert>}
      {error && <Alert variant="error">{error}</Alert>}
      {tokenRejected && <Link to="/forgot-password">Poproś o nowy link</Link>}
      <form className="auth-form" onSubmit={submit} noValidate>
        <FormField
          id="reset-password"
          label="Nowe hasło"
          type="password"
          autoComplete="new-password"
          value={password}
          onChange={(event) => setPassword(event.target.value)}
        />
        <FormField
          id="reset-confirm-password"
          label="Powtórz nowe hasło"
          type="password"
          autoComplete="new-password"
          value={confirmPassword}
          onChange={(event) => setConfirmPassword(event.target.value)}
        />
        <Button type="submit" disabled={submitting || saved}>
          {submitting ? 'Zapisywanie…' : 'Zmień hasło'}
        </Button>
      </form>
    </AuthPageLayout>
  )
}
