import { useEffect, useState } from 'react'
import { Alert, Button, Spinner } from '../../../components/ui'
import { getHackathons } from '../api/hackathonsApi'
import type { Hackathon } from '../types'
import { HackathonListItem } from './HackathonListItem'

export function HackathonList() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [requestVersion, setRequestVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function loadHackathons() {
      setIsLoading(true)
      setError(null)
      try {
        setHackathons(await getHackathons({ signal: controller.signal }))
      } catch (requestError) {
        if (requestError instanceof Error && requestError.name === 'AbortError') return
        setError('Nie udało się pobrać hackathonów. Spróbuj ponownie.')
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadHackathons()
    return () => controller.abort()
  }, [requestVersion])

  return (
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
            <HackathonListItem key={hackathon.id} hackathon={hackathon} />
          ))}
        </ul>
      )}
    </section>
  )
}
