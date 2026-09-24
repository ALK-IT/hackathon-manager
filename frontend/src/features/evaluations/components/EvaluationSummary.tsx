import type { TaskSubmissionEvaluation } from '../../registration/types'

export function EvaluationSummary({ evaluation }: { evaluation: TaskSubmissionEvaluation | null }) {
  if (!evaluation) return <p>Oczekuje na ocenę.</p>
  return (
    <div>
      <p>Ocena: {evaluation.score} / 10</p>
      <p className="evaluation-feedback">Feedback: {evaluation.feedback || 'Brak feedbacku.'}</p>
    </div>
  )
}
