import { useEffect, useState } from 'react'
import { Alert, Button, Spinner } from '../../../components/ui'
import { useTranslation } from '../../../i18n/useTranslation'
import { useAuth } from '../../auth'
import {
  deleteRegistration,
  getMyRegistration,
} from '../../registration/api/registrationApi'
import { getHackathons } from '../api/hackathonsApi'
import type { Hackathon, HackathonFilters as Filters } from '../types'
import { HackathonFilters } from './HackathonFilters'
import { HackathonListItem } from './HackathonListItem'

const PAGE_SIZE = 20

export function HackathonList() {
  const { user, isLoading: isAuthLoading } = useAuth()
  const { language, t } = useTranslation()
  const [hackathons, setHackathons] = useState<Hackathon[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [requestVersion, setRequestVersion] = useState(0)
  const [filters, setFilters] = useState<Filters>({})

  useEffect(() => {
    if (isAuthLoading) return

    const controller = new AbortController()

    async function loadHackathons() {
      setIsLoading(true)
      setError(null)
      try {
        const result = await getHackathons({
          ...filters,
          limit: PAGE_SIZE,
          offset: page * PAGE_SIZE,
          signal: controller.signal,
        })
        setHackathons(result.items)
        setTotal(result.total)
      } catch (requestError) {
        if (requestError instanceof Error && requestError.name === 'AbortError') return
        setError(t.loadHackathonsError)
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadHackathons()
    return () => controller.abort()
  }, [filters, isAuthLoading, page, requestVersion, t.loadHackathonsError, user?.public_id])

  function changeFilters(nextFilters: Filters) {
    setFilters(nextFilters)
    setPage(0)
  }

  async function withdrawRegistration(hackathon: Hackathon) {
    const registration = await getMyRegistration(hackathon.public_id)
    await deleteRegistration(registration.public_id)
    setHackathons((current) =>
      current.map((item) =>
        item.public_id === hackathon.public_id
          ? { ...item, my_registration_status: null }
          : item,
      ),
    )
  }

  return (
    <div className="hackathons-layout">
      <HackathonFilters filters={filters} language={language} onChange={changeFilters} />
      <section aria-labelledby="hackathon-list-heading">
        <h2 id="hackathon-list-heading">{t.list}</h2>

        {isLoading && <Spinner label={t.loadingHackathons} />}

        {error && (
          <div className="state-stack">
            <Alert variant="error">{error}</Alert>
            <Button type="button" onClick={() => setRequestVersion((value) => value + 1)}>
              {t.retry}
            </Button>
          </div>
        )}

        {!isLoading && !error && hackathons.length === 0 && (
          <Alert>{t.noHackathons}</Alert>
        )}

        {!isLoading && !error && hackathons.length > 0 && (
          <>
            <ul className="hackathon-list">
              {hackathons.map((hackathon) => (
                <HackathonListItem
                  key={hackathon.public_id}
                  hackathon={hackathon}
                  language={language}
                  onWithdraw={withdrawRegistration}
                />
              ))}
            </ul>
            <nav aria-label={language === 'en' ? 'Hackathon pagination' : 'Stronicowanie hackathonów'}>
              <Button
                type="button"
                variant="ghost"
                disabled={isLoading || page === 0}
                onClick={() => setPage((current) => current - 1)}
              >
                {t.previousPage}
              </Button>
              <span aria-live="polite">{t.page} {page + 1}</span>
              <Button
                type="button"
                variant="ghost"
                disabled={isLoading || (page + 1) * PAGE_SIZE >= total}
                onClick={() => setPage((current) => current + 1)}
              >
                {t.nextPage}
              </Button>
            </nav>
          </>
        )}
      </section>
    </div>
  )
}
