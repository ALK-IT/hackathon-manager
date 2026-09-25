import { useEffect, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import {
  getLeaderboard,
  setLeaderboardVisibility,
  type LeaderboardEntry,
} from '../api/evaluationsApi'
import { evaluationError } from '../utils'

const LIMITS = [3, 5, 10, 20, 50]

interface LeaderboardProps {
  hackathonId: string
  canManage?: boolean
  initiallyVisibleToParticipants?: boolean
}

export function Leaderboard({
  hackathonId,
  canManage = false,
  initiallyVisibleToParticipants = false,
}: LeaderboardProps) {
  const [limit, setLimit] = useState(10)
  const [items, setItems] = useState<LeaderboardEntry[] | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [version, setVersion] = useState(0)
  const [visibleToParticipants, setVisibleToParticipants] = useState(
    initiallyVisibleToParticipants,
  )
  const [visibilitySaving, setVisibilitySaving] = useState(false)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    void getLeaderboard(hackathonId, limit, controller.signal)
      .then((result) => {
        if (!controller.signal.aborted) setItems(result.items)
      })
      .catch((cause) => {
        if (!controller.signal.aborted) setError(evaluationError(cause))
      })
      .finally(() => {
        if (!controller.signal.aborted) setLoading(false)
      })
    return () => controller.abort()
  }, [hackathonId, limit, version])

  async function toggleVisibility() {
    setVisibilitySaving(true)
    setError(null)
    try {
      const result = await setLeaderboardVisibility(hackathonId, !visibleToParticipants)
      setVisibleToParticipants(result.visible)
    } catch (cause) {
      setError(evaluationError(cause))
    } finally {
      setVisibilitySaving(false)
    }
  }

  return <section aria-labelledby="leaderboard-heading">
    <h3 id="leaderboard-heading">Leaderboard drużyn</h3>
    <div className="leaderboard-controls">
      <label htmlFor="leaderboard-limit">Pokaż pierwszych miejsc</label>
      <select id="leaderboard-limit" value={limit}
        onChange={(event) => setLimit(Number(event.target.value))}>
        {LIMITS.map((value) => <option key={value} value={value}>{value}</option>)}
      </select>
      <Button type="button" variant="ghost" disabled={loading}
        onClick={() => setVersion((current) => current + 1)}>
        {loading ? 'Odświeżanie…' : 'Odśwież ranking'}
      </Button>
      {canManage && <Button type="button" variant={visibleToParticipants ? 'danger' : 'ghost'}
        disabled={visibilitySaving} onClick={() => void toggleVisibility()}>
        {visibilitySaving
          ? 'Zapisywanie…'
          : visibleToParticipants ? 'Ukryj przed uczestnikami' : 'Pokaż uczestnikom'}
      </Button>}
    </div>
    {error && <Alert variant="error">{error}</Alert>}
    {loading && items === null && <p role="status">Ładowanie rankingu…</p>}
    {!loading && !error && items?.length === 0 && <p>Brak drużyn w rankingu.</p>}
    {!error && items && items.length > 0 && <table className="leaderboard-table">
      <thead><tr><th scope="col">Miejsce</th><th scope="col">Drużyna</th>
        <th scope="col">Suma punktów</th><th scope="col">Ocenione zadania</th></tr></thead>
      <tbody>{items.map((item) => <tr key={item.team_public_id}>
        <td>{item.rank}</td><td>{item.team_name}</td><td>{item.total_score}</td>
        <td>{item.evaluated_tasks}</td>
      </tr>)}</tbody>
    </table>}
  </section>
}
