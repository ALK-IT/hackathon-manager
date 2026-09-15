import { Card } from '../../../components/ui'
import type { ParticipantTask } from '../../registration/types'
import { EvaluationSummary } from './EvaluationSummary'

export function ParticipantResults({ tasks }: { tasks: ParticipantTask[] }) {
  return (
    <section aria-label="Wyniki drużyny">
      <h2>Wyniki drużyny</h2>
      {tasks.length === 0 && <p>Brak opublikowanych zadań.</p>}
      {tasks.map((task) => <Card key={task.public_id}>
        <h3>{task.title}</h3>
        <p>{task.description}</p>
        {task.submission ? <>
          <a href={task.submission.github_url} target="_blank" rel="noreferrer">{task.submission.github_url}</a>
          <EvaluationSummary evaluation={task.submission.evaluation} />
        </> : <p>Nie przesłano rozwiązania.</p>}
      </Card>)}
    </section>
  )
}
