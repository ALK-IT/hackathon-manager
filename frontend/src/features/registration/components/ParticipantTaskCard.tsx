import { type FormEvent, useState } from 'react'
import { Alert, Button, Card } from '../../../components/ui'
import { saveTaskSubmission } from '../api/registrationApi'
import type { ParticipantTask, TaskSubmission } from '../types'
import { getTaskSubmissionErrorMessage } from '../utils/registrationMessages'

interface ParticipantTaskCardProps {
  hackathonPublicId: string
  task: ParticipantTask
  canSubmit: boolean
  submissionsClosed: boolean
}

export function ParticipantTaskCard({
  hackathonPublicId,
  task,
  canSubmit,
  submissionsClosed,
}: ParticipantTaskCardProps) {
  const [githubUrl, setGithubUrl] = useState(task.submission?.github_url ?? '')
  const [submission, setSubmission] = useState<TaskSubmission | null>(task.submission)
  const [isSaving, setIsSaving] = useState(false)
  const [saveError, setSaveError] = useState<string | null>(null)
  const [saveMessage, setSaveMessage] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setIsSaving(true)
    setSaveError(null)
    setSaveMessage(null)

    try {
      const savedSubmission = await saveTaskSubmission(
        hackathonPublicId,
        task.public_id,
        githubUrl,
      )
      setSubmission(savedSubmission)
      setGithubUrl(savedSubmission.github_url)
      setSaveMessage('Rozwiązanie zostało zapisane.')
    } catch (error) {
      setSaveError(getTaskSubmissionErrorMessage(error))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card className="participant-task-card">
      <h3>{task.title}</h3>
      <p>{task.description}</p>

      {submission && (
        <p>
          Aktualne rozwiązanie:{' '}
          <a href={submission.github_url} target="_blank" rel="noreferrer">
            {submission.github_url}
          </a>
        </p>
      )}

      {canSubmit && !submissionsClosed && (
        <form className="task-submission-form" onSubmit={handleSubmit}>
          <label htmlFor={`github-url-${task.public_id}`}>Link do rozwiązania na GitHubie</label>
          <input
            id={`github-url-${task.public_id}`}
            type="url"
            value={githubUrl}
            onChange={(event) => setGithubUrl(event.target.value)}
            placeholder="https://github.com/nazwa/repozytorium"
            required
          />
          <Button type="submit" disabled={isSaving} variant="ghost">
            {isSaving ? 'Zapisywanie…' : submission ? 'Zaktualizuj link' : 'Wyślij link'}
          </Button>
        </form>
      )}

      {canSubmit && submissionsClosed && <p>Termin wysyłania rozwiązań minął.</p>}
      {saveError && <Alert variant="error">{saveError}</Alert>}
      {saveMessage && <Alert variant="info">{saveMessage}</Alert>}
    </Card>
  )
}
