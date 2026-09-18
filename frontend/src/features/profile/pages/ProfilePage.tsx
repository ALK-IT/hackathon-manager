import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { useTranslation } from '../../../i18n/useTranslation'
import { useAuth } from '../../auth'
import { NotificationBell } from '../../notifications'
import { getProfileHackathons } from '../api/profileApi'
import type { ProfileHackathon } from '../types'

function initials(name: string) {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

export function ProfilePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { language: currentLanguage, t } = useTranslation()
  const [hackathons, setHackathons] = useState<ProfileHackathon[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const dateFormatter = new Intl.DateTimeFormat(currentLanguage === 'pl' ? 'pl-PL' : 'en-US', {
    day: 'numeric',
    month: 'long',
    year: 'numeric',
  })
  const statusLabels = {
    pending: t.profilePending,
    accepted: t.profileAccepted,
    rejected: t.profileRejected,
  }

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    getProfileHackathons(controller.signal)
      .then((items) => {
        if (active) setHackathons(items)
      })
      .catch((requestError: unknown) => {
        if (
          active &&
          !(requestError instanceof DOMException && requestError.name === 'AbortError')
        ) {
          setError(t.profileLoadError)
        }
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
      controller.abort()
    }
  }, [t.profileLoadError])

  if (!user) return null

  return (
    <main className="app-page profile-page">
      <nav className="profile-nav" aria-label={t.profileNavigation}>
        <Link to="/hackathons">{t.backToHackathons}</Link>
        <NotificationBell />
      </nav>

      <Card className="profile-hero">
        <div className="profile-avatar" aria-hidden="true">{initials(user.name)}</div>
        <div className="profile-identity">
          <span className="profile-eyebrow">{t.yourProfile}</span>
          <h1>{user.name}</h1>
          <p>{user.email}</p>
        </div>
        <div className="profile-hero-actions">
          <dl className="profile-meta">
            <div><dt>{t.role}</dt><dd>{user.role === 'admin' ? t.administrator : t.participant}</dd></div>
            <div><dt>{t.memberSince}</dt><dd>{dateFormatter.format(new Date(user.created_at))}</dd></div>
          </dl>
          <Button type="button" variant="ghost" onClick={() => navigate('/profile/settings')}>
            {t.settings}
          </Button>
        </div>
      </Card>

      <section className="profile-section" aria-labelledby="accepted-heading">
        <div className="profile-section-heading">
          <div>
            <span className="profile-eyebrow">{t.yourEvents}</span>
            <h2 id="accepted-heading">{t.appliedHackathons}</h2>
          </div>
          {!isLoading && !error && <span className="profile-count">{hackathons.length}</span>}
        </div>

        {isLoading && <div className="profile-state"><Spinner /> {t.loadingProfile}</div>}
        {error && <Alert variant="error">{error}</Alert>}
        {!isLoading && !error && hackathons.length === 0 && (
          <Card className="profile-empty">
            <h3>{t.noEvents}</h3>
            <p>{t.noEventsDescription}</p>
            <Link to="/hackathons">{t.findHackathon}</Link>
          </Card>
        )}
        <div className="accepted-grid">
          {hackathons.map((hackathon) => (
            <Link
              className="accepted-card-link"
              key={hackathon.registration_public_id}
              to={`/hackathons/${hackathon.hackathon_public_id}`}
            >
              <Card className="accepted-card">
                <div className="accepted-card-top">
                  <span className={`accepted-badge accepted-badge--${hackathon.status}`}>
                    {statusLabels[hackathon.status]}
                  </span>
                  <span aria-hidden="true">↗</span>
                </div>
                <h3>{hackathon.name}</h3>
                <p>{hackathon.description || t.eventDetailsFallback}</p>
                <div className="accepted-card-footer">
                  <span>{dateFormatter.format(new Date(hackathon.start_date))} – {dateFormatter.format(new Date(hackathon.end_date))}</span>
                  {hackathon.team && <span>{t.team}: {hackathon.team.name}</span>}
                </div>
              </Card>
            </Link>
          ))}
        </div>
      </section>
    </main>
  )
}
