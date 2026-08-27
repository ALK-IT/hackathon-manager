import { useEffect, useState } from 'react'
import { AppNavigation } from '../../../components/layout/AppNavigation'
import { Alert, Button, Spinner } from '../../../components/ui'
import { getMyResources } from '../api/resourcesApi'
import { ResourceCard } from '../components/ResourceCard'
import type { MyResource } from '../types'
import { getResourcesErrorMessage } from '../utils/resourceMessages'

export function MyResourcesPage() {
  const [resources, setResources] = useState<MyResource[]>([])
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [requestVersion, setRequestVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()

    async function loadResources() {
      setIsLoading(true)
      setError(null)
      try {
        setResources(await getMyResources(controller.signal))
      } catch (requestError) {
        if (requestError instanceof Error && requestError.name === 'AbortError') return
        setError(getResourcesErrorMessage(requestError))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadResources()
    return () => controller.abort()
  }, [requestVersion])

  return (
    <main className="app-page">
      <AppNavigation />
      <header className="page-header">
        <div>
          <h1>Moje zasoby</h1>
          <p>Klucze i inne zasoby przypisane Tobie lub Twojej drużynie.</p>
        </div>
      </header>

      {isLoading && <Spinner label="Ładowanie zasobów…" />}

      {error && (
        <div className="state-stack">
          <Alert variant="error">{error}</Alert>
          <Button type="button" onClick={() => setRequestVersion((value) => value + 1)}>
            Spróbuj ponownie
          </Button>
        </div>
      )}

      {!isLoading && !error && resources.length === 0 && (
        <Alert>Nie masz jeszcze przypisanych zasobów.</Alert>
      )}

      {!isLoading && !error && resources.length > 0 && (
        <ul className="resource-list">
          {resources.map((resource) => (
            <ResourceCard key={resource.public_id} resource={resource} />
          ))}
        </ul>
      )}
    </main>
  )
}
