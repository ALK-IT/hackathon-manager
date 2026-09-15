import { useEffect, useState } from 'react'
import { Alert, Button, Card } from '../../../components/ui'
import { getSubmissions, type SubmissionPage } from '../api/evaluationsApi'
import { evaluationError } from '../utils'
import { EvaluationForm } from './EvaluationForm'
import { EvaluationSummary } from './EvaluationSummary'

interface Props {
  hackathonId: string
  teamId?: string
  taskId?: string
  evaluated?: boolean
  canEvaluate: boolean
}

const LIMIT = 20

export function SubmissionList({ hackathonId, teamId, taskId, evaluated, canEvaluate }: Props) {
  const [offset, setOffset] = useState(0)
  const [version, setVersion] = useState(0)
  const [page, setPage] = useState<SubmissionPage | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [message, setMessage] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    setPage(null)
    void getSubmissions(hackathonId, {
      teamPublicId: teamId, taskPublicId: taskId, evaluated,
      limit: LIMIT, offset, signal: controller.signal,
    }).then((data) => {
      if (controller.signal.aborted) return
      const lastOffset = Math.max(0, Math.ceil(data.total / LIMIT) - 1) * LIMIT
      if (offset > lastOffset) setOffset(lastOffset)
      else setPage(data)
    }).catch((cause) => {
      if (!controller.signal.aborted) setError(evaluationError(cause))
    }).finally(() => {
      if (!controller.signal.aborted) setLoading(false)
    })
    return () => controller.abort()
  }, [hackathonId, teamId, taskId, evaluated, offset, version])

  return (
    <section aria-label="Lista rozwiązań" aria-busy={loading}>
      <Button type="button" variant="ghost" disabled={loading}
        onClick={() => setVersion((value) => value + 1)}>Odśwież rozwiązania</Button>
      {message && <p role="status">{message}</p>}
      {loading && <p role="status">Ładowanie rozwiązań…</p>}
      {error && <Alert variant="error">{error}</Alert>}
      {!loading && !error && page && (
        <>
          <p>Łącznie rozwiązań: {page.total}</p>
          {page.total === 0 && <p>Brak przesłanych rozwiązań dla wybranych filtrów.</p>}
          {page.items.map((submission) => (
            <Card key={submission.public_id}>
              <h2>{submission.team.name} — {submission.task.title}</h2>
              <a href={submission.github_url} target="_blank" rel="noreferrer">{submission.github_url}</a>
              <EvaluationSummary evaluation={submission.evaluation} />
              {canEvaluate && <EvaluationForm
                hackathonId={hackathonId} submission={submission}
                onSaved={() => {
                  setMessage('Ocena została zapisana.')
                  setVersion((value) => value + 1)
                }}
              />}
            </Card>
          ))}
          {page.total > 0 && <nav aria-label="Strony rozwiązań">
            <Button type="button" variant="ghost" disabled={offset === 0}
              onClick={() => setOffset((value) => value - LIMIT)}>Poprzednia strona</Button>
            <span> Strona {Math.floor(offset / LIMIT) + 1} z {Math.ceil(page.total / LIMIT)} </span>
            <Button type="button" variant="ghost" disabled={offset + page.items.length >= page.total}
              onClick={() => setOffset((value) => value + LIMIT)}>Następna strona</Button>
          </nav>}
        </>
      )}
    </section>
  )
}
