import { useEffect, useState } from 'react'
import { Alert, Button, Spinner } from '../../../components/ui'
import { getHackathons } from '../api/hackathonsApi'
import type { Hackathon, HackathonFilters as Filters } from '../types'
import { HackathonFilters } from './HackathonFilters'
import { HackathonListItem } from './HackathonListItem'

const PAGE_SIZE = 20

export function HackathonList() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(0)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [requestVersion, setRequestVersion] = useState(0)
  const [filters, setFilters] = useState<Filters>({})

  useEffect(() => {
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
        setError('Nie udało się pobrać hackathonów. Spróbuj ponownie.')
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadHackathons()
    return () => controller.abort()
  }, [filters, page, requestVersion])

  function changeFilters(nextFilters: Filters) {
    setFilters(nextFilters)
    setPage(0)
  }

  return (
    <div className="hackathons-layout">
      <HackathonFilters filters={filters} onChange={changeFilters} />
      <section aria-labelledby="hackathon-list-heading">
        <h2 id="hackathon-list-heading">Lista hackathonów</h2>

        {isLoading && <Spinner label="Ładowanie hackathonów…" />}

        {error && (
          <div className="state-stack">
            <Alert variant="error">{error}</Alert>
            <Button type="button" onClick={() => setRequestVersion((value) => value + 1)}>
              Spróbuj ponownie
            </Button>
          </div>
        )}

        {!isLoading && !error && hackathons.length === 0 && (
          <Alert>Brak hackathonów do wyświetlenia.</Alert>
        )}

        {!isLoading && !error && hackathons.length > 0 && (
          <>
            <ul className="hackathon-list">
              {hackathons.map((hackathon) => (
                <HackathonListItem key={hackathon.public_id} hackathon={hackathon} />
              ))}
            </ul>
            <nav aria-label="Stronicowanie hackathonów">
              <Button
                type="button"
                variant="ghost"
                disabled={isLoading || page === 0}
                onClick={() => setPage((current) => current - 1)}
              >
                Poprzednia strona
              </Button>
              <span aria-live="polite">Strona {page + 1}</span>
              <Button
                type="button"
                variant="ghost"
                disabled={isLoading || (page + 1) * PAGE_SIZE >= total}
                onClick={() => setPage((current) => current + 1)}
              >
                Następna strona
              </Button>
            </nav>
          </>
        )}
      </section>
    </div>
  )
}
