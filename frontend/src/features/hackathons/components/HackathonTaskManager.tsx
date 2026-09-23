import { useEffect, useState, type FormEvent } from 'react'
import { Alert, Button, Spinner } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import {
  createHackathonTask,
  getHackathonTasks,
} from '../api/hackathonsApi'
import type { HackathonTask } from '../types'
import { useTranslation } from '../../../i18n/useTranslation'
import {
  getCreateHackathonTaskErrorMessage,
  getHackathonTasksErrorMessage,
} from '../utils/hackathonMessages'

interface HackathonTaskManagerProps {
  hackathonPublicId: string
  hackathonStartDate: string
  hackathonEndDate: string
}

function toLocalDateTime(value: string): string {
  const date = new Date(value)
  const offset = date.getTimezoneOffset() * 60_000
  return new Date(date.getTime() - offset).toISOString().slice(0, 16)
}

export function HackathonTaskManager({
  hackathonPublicId,
  hackathonStartDate,
  hackathonEndDate,
}: HackathonTaskManagerProps) {
  const { language, t } = useTranslation()
  const [tasks, setTasks] = useState<HackathonTask[]>([])
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [visibleFrom, setVisibleFrom] = useState(() => toLocalDateTime(hackathonStartDate))
  const [isLoading, setIsLoading] = useState(true)
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [submitError, setSubmitError] = useState<string | null>(null)
  const [successMessage, setSuccessMessage] = useState<string | null>(null)

  useEffect(() => {
    const controller = new AbortController()

    async function loadTasks() {
      try {
        setTasks(await getHackathonTasks(hackathonPublicId, controller.signal))
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
        setLoadError(getHackathonTasksErrorMessage(error, language))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadTasks()
    return () => controller.abort()
  }, [hackathonPublicId, language])

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setSubmitError(null)
    setSuccessMessage(null)

    const normalizedTitle = title.trim()
    const normalizedDescription = description.trim()
    if (!normalizedTitle || !normalizedDescription || !visibleFrom) {
      setSubmitError(language === 'en' ? 'Enter the task name, description, and publication date.' : 'Uzupełnij nazwę, opis i termin publikacji zadania.')
      return
    }
    if (Date.parse(visibleFrom) >= Date.parse(hackathonEndDate)) {
      setSubmitError(language === 'en' ? 'The publication date must be before the hackathon ends.' : 'Termin publikacji musi przypadać przed zakończeniem hackathonu.')
      return
    }

    setIsSubmitting(true)
    try {
      const task = await createHackathonTask(hackathonPublicId, {
        title: normalizedTitle,
        description: normalizedDescription,
        visible_from: new Date(visibleFrom).toISOString(),
      })
      setTasks((current) =>
        [...current, task].sort(
          (first, second) =>
            Date.parse(first.visible_from) - Date.parse(second.visible_from),
        ),
      )
      setTitle('')
      setDescription('')
      setSuccessMessage(language === 'en' ? 'Task added.' : 'Zadanie zostało dodane.')
    } catch (error) {
      setSubmitError(getCreateHackathonTaskErrorMessage(error, language))
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <section aria-labelledby="hackathon-tasks-heading">
      <h2 id="hackathon-tasks-heading">{t.tasks}</h2>

      {isLoading && <Spinner label={t.loadingTasks} />}
      {loadError && <Alert variant="error">{loadError}</Alert>}
      {!isLoading && !loadError && tasks.length === 0 && <p>{t.noTasks}</p>}
      {tasks.length > 0 && (
        <ul className="hackathon-task-list">
          {tasks.map((task) => (
            <li key={task.public_id}>
              <strong>{task.title}</strong>
              <p>{task.description}</p>
              <small>
                {t.visibleFrom}: {new Date(task.visible_from).toLocaleString(language === 'en' ? 'en-US' : 'pl-PL')}
              </small>
            </li>
          ))}
        </ul>
      )}

      <form className="hackathon-task-form" onSubmit={handleSubmit} noValidate>
        <FormField
          id="task-title"
          label={t.taskName}
          value={title}
          maxLength={200}
          required
          onChange={(event) => setTitle(event.target.value)}
        />
        <div className="form-field">
          <label htmlFor="task-description">{t.taskDescription}</label>
          <textarea
            id="task-description"
            value={description}
            maxLength={10_000}
            rows={5}
            required
            onChange={(event) => setDescription(event.target.value)}
          />
        </div>
        <div className="task-visibility-field">
          <FormField
            id="task-visible-from"
            label={t.visibleToParticipantsFrom}
            type="datetime-local"
            value={visibleFrom}
            max={toLocalDateTime(hackathonEndDate)}
            required
            onChange={(event) => setVisibleFrom(event.target.value)}
          />
          <Button
            type="button"
            variant="ghost"
            onClick={() => setVisibleFrom(toLocalDateTime(hackathonStartDate))}
          >
            {t.hackathonStart}
          </Button>
        </div>
        {submitError && <Alert variant="error">{submitError}</Alert>}
        {successMessage && <Alert>{successMessage}</Alert>}
        <Button type="submit" variant="ghost" disabled={isSubmitting}>
          {isSubmitting ? t.adding : t.addTask}
        </Button>
      </form>
    </section>
  )
}
