import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { useAuth } from '../../auth'
import { getProfileHackathons } from '../api/profileApi'
import type { ProfileHackathon, RegistrationStatus } from '../types'

const dateFormatter = new Intl.DateTimeFormat('pl-PL', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})

function initials(name: string) {
  return name
    .split(/\s+/)
    .slice(0, 2)
    .map((part) => part[0])
    .join('')
    .toUpperCase()
}

const statusLabels: Record<RegistrationStatus, string> = {
  pending: 'Oczekuje',
  accepted: 'Przyjęty',
  rejected: 'Odrzucony',
}

const PROFILE_HACKATHONS_PAGE_SIZE = 12

export function ProfilePage() {
  const { user } = useAuth()
  const [hackathons, setHackathons] = useState<ProfileHackathon[]>([])
  const [total, setTotal] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [isLoadingMore, setIsLoadingMore] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [loadMoreError, setLoadMoreError] = useState<string | null>(null)

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
          setError('Nie udało się pobrać Twoich hackathonów.')
        }
      })
      .finally(() => {
        if (active) setIsLoading(false)
      })
    return () => {
      active = false
      controller.abort()
    }
  }, [])

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
      setLoadMoreError('Nie udało się pobrać kolejnych hackathonów.')
    } finally {
      setIsLoadingMore(false)
    }
  }

  if (!user) return null

  return (
    <main className="app-page profile-page">
      <nav className="profile-nav" aria-label="Nawigacja profilu">
        <Link to="/hackathons">← Wszystkie hackathony</Link>
      </nav>

      <Card className="profile-hero">
        <div className="profile-avatar" aria-hidden="true">{initials(user.name)}</div>
        <div className="profile-identity">
          <span className="profile-eyebrow">Twój profil</span>
          <h1>{user.name}</h1>
          <p>{user.email}</p>
        </div>
        <dl className="profile-meta">
          <div><dt>Rola</dt><dd>{user.role === 'admin' ? 'Administrator' : 'Uczestnik'}</dd></div>
          <div><dt>W serwisie od</dt><dd>{dateFormatter.format(new Date(user.created_at))}</dd></div>
        </dl>
      </Card>

      <section className="profile-section" aria-labelledby="accepted-heading">
        <div className="profile-section-heading">
          <div>
            <span className="profile-eyebrow">Twoje wydarzenia</span>
            <h2 id="accepted-heading">Hackathony, na które aplikujesz</h2>
          </div>
          {!isLoading && !error && <span className="profile-count">{total}</span>}
        </div>

        {isLoading && <div className="profile-state"><Spinner /> Pobieramy hackathony…</div>}
        {error && <Alert variant="error">{error}</Alert>}
        {!isLoading && !error && hackathons.length === 0 && (
          <Card className="profile-empty">
            <h3>Jeszcze nie ma tu żadnych wydarzeń</h3>
            <p>Gdy wyślesz pierwsze zgłoszenie, hackathon pojawi się w tym miejscu.</p>
            <Link to="/hackathons">Znajdź hackathon</Link>
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
                <p>{hackathon.description || 'Szczegóły wydarzenia znajdziesz na stronie hackathonu.'}</p>
                <div className="accepted-card-footer">
                  <span>{dateFormatter.format(new Date(hackathon.start_date))} – {dateFormatter.format(new Date(hackathon.end_date))}</span>
                  {hackathon.team && <span>Zespół: {hackathon.team.name}</span>}
                </div>
              </Card>
            </Link>
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
              {isLoadingMore ? 'Pobieranie…' : 'Pokaż więcej'}
            </Button>
          </div>
        )}
      </section>
    </main>
  )
}
