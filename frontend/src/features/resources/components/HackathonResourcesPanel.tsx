import { useEffect, useState } from 'react'
import { Alert, Button, Spinner } from '../../../components/ui'
import { getMyResources } from '../api/resourcesApi'
import type { MyResource } from '../types'
import { getResourcesErrorMessage } from '../utils/resourceMessages'
import { ResourceCard } from './ResourceCard'

interface HackathonResourcesPanelProps {
  hackathonPublicId: string
}

export function HackathonResourcesPanel({
  hackathonPublicId,
}: HackathonResourcesPanelProps) {
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
        const assignedResources = await getMyResources(controller.signal)
        setResources(
          assignedResources.filter(
            (resource) => resource.hackathon.public_id === hackathonPublicId,
          ),
        )
      } catch (requestError) {
        if (requestError instanceof Error && requestError.name === 'AbortError') return
        setError(getResourcesErrorMessage(requestError))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadResources()
    return () => controller.abort()
  }, [hackathonPublicId, requestVersion])

  return (
    <section aria-labelledby="hackathon-resources-heading">
      <h2 id="hackathon-resources-heading">Moje zasoby</h2>
      <p>Zasoby przypisane Tobie lub Twojej drużynie w tym hackathonie.</p>

      {isLoading && <Spinner label="Ładowanie zasobów…" />}

      {error && (
        <div className="state-stack">
          <Alert variant="error">{error}</Alert>
          <Button
            type="button"
            onClick={() => setRequestVersion((value) => value + 1)}
          >
            Spróbuj ponownie
          </Button>
        </div>
      )}

      {!isLoading && !error && resources.length === 0 && (
        <Alert>Nie masz jeszcze zasobów przypisanych do tego hackathonu.</Alert>
      )}

      {!isLoading && !error && resources.length > 0 && (
        <ul className="resource-list">
          {resources.map((resource) => (
            <ResourceCard key={resource.public_id} resource={resource} />
          ))}
        </ul>
      )}
    </section>
  )
}
