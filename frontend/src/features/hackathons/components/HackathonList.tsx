import { useEffect, useState } from 'react'
import { Alert, Button, Spinner } from '../../../components/ui'
import { useAuth } from '../../auth'
import { getHackathons } from '../api/hackathonsApi'
import type { Hackathon, HackathonFilters as Filters } from '../types'
import { HackathonFilters } from './HackathonFilters'
import { HackathonListItem } from './HackathonListItem'

export function HackathonList() {
  const { user, isLoading: isAuthLoading } = useAuth()
  const [hackathons, setHackathons] = useState<Hackathon[]>([])
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
        setHackathons(
          await getHackathons({
            ...filters,
            signal: controller.signal,
          }),
        )
      } catch (requestError) {
        if (requestError instanceof Error && requestError.name === 'AbortError') return
        setError('Nie udało się pobrać hackathonów. Spróbuj ponownie.')
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadHackathons()
    return () => controller.abort()
  }, [filters, isAuthLoading, requestVersion, user?.public_id])

  return (
    <div className="hackathons-layout">
      <HackathonFilters filters={filters} onChange={setFilters} />
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
          <ul className="hackathon-list">
            {hackathons.map((hackathon) => (
              <HackathonListItem key={hackathon.public_id} hackathon={hackathon} />
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
