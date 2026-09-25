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
  const [scores, setScores] = useState(() => submission.task.criteria.map((_, index) =>
    submission.evaluation?.criterion_scores.find((item) => item.criterion_index === index)?.points.toString() ?? ''))
  const [feedback, setFeedback] = useState(submission.evaluation?.feedback ?? '')
  const [saving, setSaving] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const pending = useRef(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    if (pending.current) return
    const values = scores.map(Number)
    if (submission.task.criteria.length === 0 || values.some((value, index) =>
      !scores[index].trim() || !Number.isFinite(value) || value < 0 ||
      value > submission.task.criteria[index].max_points ||
      Math.abs(value * 100 - Math.round(value * 100)) > 0.000001) || feedback.length > 10000) {
      setError('Oceń każde kryterium w jego zakresie (maksymalnie dwa miejsca po przecinku).')
      return
    }
    pending.current = true
    setSaving(true)
    setError(null)
    try {
      await saveEvaluation(hackathonId, submission.task.public_id, submission.public_id,
        { criterion_scores: values.map((points, criterion_index) => ({ criterion_index, points })),
          feedback: feedback.trim() || null })
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
      <fieldset>
        <legend>Ocena według kryteriów</legend>
        {submission.task.criteria.map((criterion, index) => <div key={`${criterion.name}-${index}`}>
          <label htmlFor={`${id}-criterion-${index}`}>{criterion.name} (0–{criterion.max_points} pkt)</label>
          {criterion.description && <p>{criterion.description}</p>}
          <input id={`${id}-criterion-${index}`} type="number" min="0" max={criterion.max_points}
            step="0.01" required value={scores[index]} disabled={saving}
            onChange={(event) => setScores((current) => current.map((value, itemIndex) =>
              itemIndex === index ? event.target.value : value))} />
        </div>)}
        {submission.task.criteria.length === 0 && <Alert variant="error">
          To zadanie nie ma kryteriów. Dodaj kryteria w zakładce Zadania przed oceną.
        </Alert>}
        <p>Łączna ocena: {scores.reduce((total, value) => total + (Number(value) || 0), 0)} / {' '}
          {submission.task.criteria.reduce((total, criterion) => total + criterion.max_points, 0)}</p>
      </fieldset>
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
