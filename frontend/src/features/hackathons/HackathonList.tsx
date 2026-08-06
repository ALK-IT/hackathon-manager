import { useEffect, useState } from 'react'
import { Alert } from '../../design-system/Alert'
import { Card } from '../../design-system/Card'
import { Spinner } from '../../design-system/Spinner'
import { colors, spacing, typography } from '../../design-system/tokens'

const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

interface Hackathon {
  id: number
  name: string
}

export function HackathonList() {
  const [hackathons, setHackathons] = useState<Hackathon[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadHackathons() {
      try {
        const response = await fetch(`${API_URL}/api/hackathons`, {
          signal: controller.signal,
        })

        if (!response.ok) {
          throw new Error(`Request failed with status ${response.status}`)
        }

        const data: Hackathon[] = await response.json()
        setHackathons(data)
      } catch (requestError) {
        if (requestError instanceof Error && requestError.name === 'AbortError') {
          return
        }

        setError('Failed to load hackathons. Please try again later.')
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false)
        }
      }
    }

    void loadHackathons()

    return () => controller.abort()
  }, [])

  return (
    <section
      aria-labelledby="hackathons-heading"
      style={{
        color: colors.text,
        fontFamily: typography.fontFamily,
        padding: spacing.lg,
      }}
    >
      <h2 id="hackathons-heading">Hackathony</h2>

      {loading && <Spinner label="Loading hackathons…" />}

      {error && <Alert variant="error">{error}</Alert>}

      {!loading && !error && (
        <ul
          style={{
            display: 'grid',
            gap: spacing.sm,
            listStyle: 'none',
            margin: 0,
            padding: 0,
          }}
        >
          {hackathons.map((hackathon) => (
            <li key={hackathon.id}>
              <Card>
                #{hackathon.id} — {hackathon.name}
              </Card>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
