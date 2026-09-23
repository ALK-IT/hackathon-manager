import { useEffect, useState, type FormEvent } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Card } from '../../../components/ui'
import { useTranslation } from '../../../i18n/useTranslation'
import { useAuth, type Language } from '../../auth'
import { sendPasswordResetLink } from '../api/profileApi'

export function ProfileSettingsPage() {
  const { user, updateSettings } = useAuth()
  const { t } = useTranslation()
  const [name, setName] = useState(user?.name ?? '')
  const [language, setLanguage] = useState<Language>(user?.language ?? 'pl')
  const [isSaving, setIsSaving] = useState(false)
  const [isSendingPasswordLink, setIsSendingPasswordLink] = useState(false)
  const [message, setMessage] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (!user) return
    setName(user.name)
    setLanguage(user.language)
  }, [user])

  if (!user) return null
  const userEmail = user.email

  async function saveSettings(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setMessage(null)
    setError(null)
    try {
      await updateSettings({ name, language })
      setMessage(t.settingsSaved)
    } catch {
      setError(t.settingsError)
    } finally {
      setIsSaving(false)
    }
  }

  async function requestPasswordChange() {
    setIsSendingPasswordLink(true)
    setMessage(null)
    setError(null)
    try {
      await sendPasswordResetLink(userEmail)
      setMessage(t.passwordLinkSent)
    } catch {
      setError(t.passwordLinkError)
    } finally {
      setIsSendingPasswordLink(false)
    }
  }

  return (
    <main className="app-page profile-page">
      <nav className="profile-nav" aria-label={t.settings}>
        <Link to="/profile">{t.backToProfile}</Link>
      </nav>
      <div className="profile-section-heading">
        <div>
          <span className="profile-eyebrow">{t.yourProfile}</span>
          <h1>{t.accountSettings}</h1>
        </div>
      </div>
      <Card className="profile-settings-card">
        <form className="profile-settings-form" onSubmit={saveSettings}>
          <label className="form-field" htmlFor="profile-name">
            <span>{t.username}</span>
            <input
              id="profile-name"
              value={name}
              minLength={3}
              maxLength={100}
              required
              autoComplete="username"
              onChange={(event) => setName(event.target.value)}
            />
          </label>
          <label className="form-field" htmlFor="profile-language">
            <span>{t.language}</span>
            <select
              id="profile-language"
              value={language}
              onChange={(event) => setLanguage(event.target.value as Language)}
            >
              <option value="pl">{t.polish}</option>
              <option value="en">{t.english}</option>
            </select>
          </label>
          <Button type="submit" disabled={isSaving}>
            {isSaving ? t.saving : t.saveSettings}
          </Button>
        </form>
        <div className="profile-password-settings">
          <h2>{t.password}</h2>
          <p>{t.passwordDescription}</p>
          <Button
            type="button"
            variant="ghost"
            disabled={isSendingPasswordLink}
            onClick={() => void requestPasswordChange()}
          >
            {isSendingPasswordLink ? t.sending : t.sendPasswordLink}
          </Button>
        </div>
        {message && <Alert>{message}</Alert>}
        {error && <Alert variant="error">{error}</Alert>}
      </Card>
    </main>
  )
}
