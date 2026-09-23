import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AppNavigation } from '../../../components/layout/AppNavigation'
import { Button } from '../../../components/ui'
import { setStoredLanguage, useTranslation } from '../../../i18n/useTranslation'
import { useAuth } from '../../auth'
import { NotificationBell } from '../../notifications'
import { HackathonList } from '../components/HackathonList'

export function HackathonsPage() {
  const { user, isLoading, logout, updateSettings } = useAuth()
  const { language, t } = useTranslation()
  const [isChangingLanguage, setIsChangingLanguage] = useState(false)
  const navigate = useNavigate()

  async function handleLogout() {
    await logout()
    navigate('/', { replace: true })
  }

  async function toggleLanguage() {
    const nextLanguage = language === 'en' ? 'pl' : 'en'
    if (!user) {
      setStoredLanguage(nextLanguage)
      return
    }

    setIsChangingLanguage(true)
    try {
      await updateSettings({ name: user.name, language: nextLanguage })
    } finally {
      setIsChangingLanguage(false)
    }
  }

  return (
    <main className="app-page">
      <AppNavigation />
      <header className="page-header">
        <div>
          <h1>{t.hackathons}</h1>
          {user && <p>{t.loggedInAs}: {user.email}</p>}
        </div>
        {user ? (
          <div className="page-header-actions">
            <NotificationBell />
            <span>{t.role}: {user.role}</span>
            <Link to="/profile">{t.profile}</Link>
            {user.role === 'admin' && (
              <Button
                type="button"
                variant="ghost"
                onClick={() => navigate('/hackathons/create')}
              >
                {t.createHackathon}
              </Button>
            )}
            <Button type="button" variant="ghost" onClick={() => void handleLogout()}>
              {t.logout}
            </Button>
          </div>
        ) : (
          !isLoading && <Link to="/login">{t.login}</Link>
        )}
        <Button
          type="button"
          variant="ghost"
          aria-label={t.changeLanguage}
          disabled={isChangingLanguage}
          onClick={() => void toggleLanguage()}
        >
          ENG / POL
        </Button>
      </header>
      {!isLoading && <HackathonList />}
    </main>
  )
}
