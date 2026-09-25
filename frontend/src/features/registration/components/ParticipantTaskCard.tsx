import { type FormEvent, useState } from 'react'
import { Alert, Button, Card } from '../../../components/ui'
import { saveTaskSubmission } from '../api/registrationApi'
import type { ParticipantTask, TaskSubmission } from '../types'
import { getTaskSubmissionErrorMessage } from '../utils/registrationMessages'
import { useTranslation } from '../../../i18n/useTranslation'

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
  const { language, t } = useTranslation()
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
      setSaveMessage(t.solutionSaved)
    } catch (error) {
      setSaveError(getTaskSubmissionErrorMessage(error, language))
    } finally {
      setIsSaving(false)
    }
  }

  return (
    <Card className="participant-task-card">
      <h3>{task.title}</h3>
      <p>{task.description}</p>
      {task.criteria.length > 0 && <section aria-label={language === 'en' ? 'Evaluation criteria' : 'Kryteria oceny'}>
        <h4>{language === 'en' ? 'Evaluation criteria' : 'Kryteria oceny'}</h4>
        <ul>
          {task.criteria.map((criterion, index) => <li key={`${criterion.name}-${index}`}>
            <strong>{criterion.name}</strong> — {criterion.max_points} {language === 'en' ? 'points' : 'pkt'}
            {criterion.description && <p>{criterion.description}</p>}
          </li>)}
        </ul>
      </section>}

      {submission && (
        <p>
          {t.solution}:{' '}
          <a href={submission.github_url} target="_blank" rel="noreferrer">
            {submission.github_url}
          </a>
        </p>
      )}

      {canSubmit && !submissionsClosed && (
        <form className="task-submission-form" onSubmit={handleSubmit}>
          <label htmlFor={`github-url-${task.public_id}`}>{t.githubSolutionLink}</label>
          <input
            id={`github-url-${task.public_id}`}
            type="url"
            value={githubUrl}
            onChange={(event) => setGithubUrl(event.target.value)}
            placeholder="https://github.com/username/repository"
            required
          />
          <Button type="submit" disabled={isSaving} variant="ghost">
            {isSaving ? t.saving : submission ? t.updateLink : t.submitLink}
          </Button>
        </form>
      )}

      {canSubmit && submissionsClosed && <p>{t.submissionsClosed}</p>}
      {saveError && <Alert variant="error">{saveError}</Alert>}
      {saveMessage && <Alert variant="info">{saveMessage}</Alert>}
    </Card>
  )
}
