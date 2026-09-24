import { useId, useRef, useState, type FormEvent } from 'react'
import { Alert, Button } from '../../../components/ui'
import { saveEvaluation, type SubmissionWithTask } from '../api/evaluationsApi'
import { evaluationError } from '../utils'

interface Props {
  hackathonId: string
  submission: SubmissionWithTask
  onSaved: () => void
}

export function EvaluationForm({ hackathonId, submission, onSaved }: Props) {
  const id = useId()
  const [score, setScore] = useState(submission.evaluation?.score.toString() ?? '')
  const [feedback, setFeedback] = useState(submission.evaluation?.feedback ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pending = useRef(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (pending.current) return
    const value = Number(score)
    if (!score.trim() || !Number.isFinite(value) || value < 0 || value > 10 ||
      Math.abs(value * 100 - Math.round(value * 100)) > 0.000001 || feedback.length > 10000) {
      setError('Podaj ocenę od 0 do 10 (maksymalnie dwa miejsca po przecinku) i feedback do 10000 znaków.')
      return
    }
    pending.current = true
    setSaving(true)
    setError(null)
    try {
      await saveEvaluation(hackathonId, submission.task.public_id, submission.public_id,
        { score: value, feedback: feedback.trim() || null })
      onSaved()
    } catch (cause) {
      setError(evaluationError(cause))
    } finally {
      pending.current = false
      setSaving(false)
    }
  }

  return (
    <form className="task-submission-form" onSubmit={submit}>
      <label htmlFor={`${id}-score`}>Ocena (0–10)</label>
      <input id={`${id}-score`} type="number" min="0" max="10" step="0.01" required
        value={score} disabled={saving} onChange={(event) => setScore(event.target.value)} />
      <label htmlFor={`${id}-feedback`}>Feedback (opcjonalnie)</label>
      <textarea id={`${id}-feedback`} maxLength={10000} value={feedback} disabled={saving}
        onChange={(event) => setFeedback(event.target.value)} />
      {error && <Alert variant="error">{error}</Alert>}
      <Button variant="ghost" type="submit" disabled={saving}>
        {saving ? 'Zapisywanie…' : 'Zapisz ocenę'}
      </Button>
    </form>
  )
}
