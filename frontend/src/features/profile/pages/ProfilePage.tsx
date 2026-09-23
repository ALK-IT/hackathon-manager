import { useEffect, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { useTranslation } from '../../../i18n/useTranslation'
import { useAuth } from '../../auth'
import { NotificationBell } from '../../notifications'
import { deleteRegistration } from '../../registration/api/registrationApi'
import { WithdrawRegistrationButton } from '../../registration/components/WithdrawRegistrationButton'
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

const PROFILE_HACKATHONS_PAGE_SIZE = 12
export function ProfilePage() {
  const { user } = useAuth()
  const navigate = useNavigate()
  const { language: currentLanguage, t } = useTranslation()
  const [hackathons, setHackathons] = useState<ProfileHackathon[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
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
  const [loadMoreError, setLoadMoreError] = useState<string | null>(null)
  const [loadedAt] = useState(() => Date.now())

  useEffect(() => {
    const controller = new AbortController()
    let active = true
    getProfileHackathons(PROFILE_HACKATHONS_PAGE_SIZE, 0, controller.signal)
      .then((response) => {
        if (active) {
          setHackathons(response.items)
          setTotal(response.total)
        }
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

  async function loadMoreHackathons() {
    setIsLoadingMore(true)
    setLoadMoreError(null)
    try {
      const response = await getProfileHackathons(
        PROFILE_HACKATHONS_PAGE_SIZE,
        hackathons.length,
      )
      setHackathons((current) => {
        const knownRegistrationIds = new Set(
          current.map((hackathon) => hackathon.registration_public_id),
        )
        return [
          ...current,
          ...response.items.filter(
            (hackathon) =>
              !knownRegistrationIds.has(hackathon.registration_public_id),
          ),
        ]
      })
      setTotal(response.total)
    } catch {
      setLoadMoreError(t.profileLoadMoreError)
    } finally {
      setIsLoadingMore(false)
    }
  }

  async function withdrawRegistration(registrationPublicId: string) {
    await deleteRegistration(registrationPublicId)
    setHackathons((current) =>
      current.filter(
        (hackathon) => hackathon.registration_public_id !== registrationPublicId,
      ),
    )
    setTotal((current) => Math.max(0, current - 1))
  }

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

      <section className="profile-section" aria-labelledby="registrations-heading">
        <div className="profile-section-heading">
          <div>
            <span className="profile-eyebrow">{t.yourEvents}</span>
            <h2 id="registrations-heading">{t.appliedHackathons}</h2>
          </div>
          {!isLoading && !error && <span className="profile-count">{total}</span>}
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
        <div className="registration-grid">
          {hackathons.map((hackathon) => (
            <Card
              className="registration-card"
              key={hackathon.registration_public_id}
            >
              <Link
                className="registration-card-link"
                to={`/hackathons/${hackathon.hackathon_public_id}`}
              >
                <div className="registration-card-top">
                  <span className={`registration-status-badge registration-status-badge--${hackathon.status}`}>
                    {statusLabels[hackathon.status]}
                  </span>
                  <span aria-hidden="true">↗</span>
                </div>
                <h3>{hackathon.name}</h3>
                <p>{hackathon.description || t.eventDetailsFallback}</p>
                <div className="registration-card-footer">
                  <span>{dateFormatter.format(new Date(hackathon.start_date))} – {dateFormatter.format(new Date(hackathon.end_date))}</span>
                  {hackathon.team && <span>{t.team}: {hackathon.team.name}</span>}
                </div>
              </Link>
              {loadedAt < Date.parse(hackathon.end_date) && (
                <WithdrawRegistrationButton
                  language={currentLanguage}
                  onWithdraw={() =>
                    withdrawRegistration(hackathon.registration_public_id)
                  }
                />
              )}
            </Card>
          ))}
        </div>
        {loadMoreError && <Alert variant="error">{loadMoreError}</Alert>}
        {!isLoading && !error && hackathons.length < total && (
          <div className="profile-load-more">
            <Button
              variant="ghost"
              disabled={isLoadingMore}
              onClick={() => void loadMoreHackathons()}
            >
              {isLoadingMore ? t.loadingMore : t.showMore}
            </Button>
          </div>
        )}
      </section>
    </main>
  )
}
