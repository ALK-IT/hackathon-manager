import type { TaskSubmissionEvaluation } from '../../registration/types'
import type { TaskCriterion } from '../../registration/types'

export function EvaluationSummary({ evaluation, criteria = [] }: {
  evaluation: TaskSubmissionEvaluation | null
  criteria?: TaskCriterion[]
}) {
  if (!evaluation) return <p>Oczekuje na ocenę.</p>
  const maximum = criteria.reduce((total, criterion) => total + criterion.max_points, 0)
  return (
    <div>
      <p>Ocena: {evaluation.score}{maximum > 0 ? ` / ${maximum}` : ''}</p>
      {evaluation.criterion_scores.length > 0 && <ul>
        {evaluation.criterion_scores.map((item) => <li key={item.criterion_index}>
          {criteria[item.criterion_index]?.name ?? `Kryterium ${item.criterion_index + 1}`}: {item.points}
          {criteria[item.criterion_index] ? ` / ${criteria[item.criterion_index].max_points}` : ''}
        </li>)}
      </ul>}
      <p className="evaluation-feedback">Feedback: {evaluation.feedback || 'Brak feedbacku.'}</p>
    </div>
  )
}
