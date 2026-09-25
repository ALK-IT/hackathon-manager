import { useEffect, useState, type FormEvent } from 'react'
import { Alert, Button, Spinner } from '../../../components/ui'
import { FormField } from '../../auth/components/FormField'
import {
  createHackathonTask,
  getHackathonTasks,
  updateHackathonTask,
} from '../api/hackathonsApi'
import type { HackathonTask, HackathonTaskCriterion } from '../types'
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

const emptyCriterion = (): HackathonTaskCriterion => ({
  name: '',
  description: '',
  max_points: 10,
})

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
  const [criteria, setCriteria] = useState<HackathonTaskCriterion[]>([])
  const [editingTaskId, setEditingTaskId] = useState<string | null>(null)
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
    const normalizedCriteria = criteria.map((criterion) => ({
      name: criterion.name.trim(),
      description: criterion.description.trim(),
      max_points: Number(criterion.max_points),
    }))
    if (normalizedCriteria.some((criterion) => !criterion.name ||
      !Number.isInteger(criterion.max_points) || criterion.max_points < 1 || criterion.max_points > 1000)) {
      setSubmitError(language === 'en'
        ? 'Each criterion needs a name and a point limit from 1 to 1000.'
        : 'Każde kryterium musi mieć nazwę i limit punktów od 1 do 1000.')
      return
    }

    setIsSubmitting(true)
    try {
      const payload = {
        title: normalizedTitle,
        description: normalizedDescription,
        visible_from: new Date(visibleFrom).toISOString(),
        criteria: normalizedCriteria,
      }
      const task = editingTaskId
        ? await updateHackathonTask(hackathonPublicId, editingTaskId, payload)
        : await createHackathonTask(hackathonPublicId, payload)
      setTasks((current) => {
        const next = editingTaskId
          ? current.map((item) => item.public_id === editingTaskId ? task : item)
          : [...current, task]
        return next.sort(
          (first, second) =>
            Date.parse(first.visible_from) - Date.parse(second.visible_from),
        )
      })
      setTitle('')
      setDescription('')
      setVisibleFrom(toLocalDateTime(hackathonStartDate))
      setCriteria([])
      setEditingTaskId(null)
      setSuccessMessage(editingTaskId
        ? (language === 'en' ? 'Task updated.' : 'Zadanie zostało zaktualizowane.')
        : (language === 'en' ? 'Task added.' : 'Zadanie zostało dodane.'))
    } catch (error) {
      setSubmitError(getCreateHackathonTaskErrorMessage(error, language))
    } finally {
      setIsSubmitting(false)
    }
  }

  function startEditing(task: HackathonTask) {
    setEditingTaskId(task.public_id)
    setTitle(task.title)
    setDescription(task.description)
    setVisibleFrom(toLocalDateTime(task.visible_from))
    setCriteria(task.criteria.map((criterion) => ({ ...criterion })))
    setSubmitError(null)
    setSuccessMessage(null)
  }

  function cancelEditing() {
    setEditingTaskId(null)
    setTitle('')
    setDescription('')
    setVisibleFrom(toLocalDateTime(hackathonStartDate))
    setCriteria([])
    setSubmitError(null)
  }

  function updateCriterion(index: number, update: Partial<HackathonTaskCriterion>) {
    setCriteria((current) => current.map((criterion, criterionIndex) =>
      criterionIndex === index ? { ...criterion, ...update } : criterion))
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
              {task.criteria.length > 0 && <div>
                <strong>{language === 'en' ? 'Evaluation criteria' : 'Kryteria oceny'}</strong>
                <ul>
                  {task.criteria.map((criterion, index) => <li key={`${criterion.name}-${index}`}>
                    {criterion.name} — {criterion.max_points} {language === 'en' ? 'points' : 'pkt'}
                    {criterion.description && <p>{criterion.description}</p>}
                  </li>)}
                </ul>
              </div>}
              <Button type="button" variant="ghost" onClick={() => startEditing(task)}>
                {language === 'en' ? 'Edit task' : 'Edytuj zadanie'}
              </Button>
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
        <fieldset className="task-criteria-fieldset">
          <legend>{language === 'en' ? 'Evaluation criteria' : 'Kryteria oceny'}</legend>
          {criteria.length === 0 && <p>{language === 'en'
            ? 'No custom criteria. You can add them below.'
            : 'Brak własnych kryteriów. Możesz dodać je poniżej.'}</p>}
          {criteria.map((criterion, index) => <div className="task-criterion-row" key={index}>
            <FormField id={`task-criterion-name-${index}`} label={language === 'en' ? 'Criterion name' : 'Nazwa kryterium'}
              value={criterion.name} maxLength={200} required
              onChange={(event) => updateCriterion(index, { name: event.target.value })} />
            <FormField id={`task-criterion-points-${index}`} label={language === 'en' ? 'Maximum points' : 'Maksymalna liczba punktów'}
              type="number" min={1} max={1000} value={criterion.max_points} required
              onChange={(event) => updateCriterion(index, { max_points: Number(event.target.value) })} />
            <div className="form-field">
              <label htmlFor={`task-criterion-description-${index}`}>{language === 'en' ? 'Criterion description' : 'Opis kryterium'}</label>
              <textarea id={`task-criterion-description-${index}`} rows={2} maxLength={2000}
                value={criterion.description}
                onChange={(event) => updateCriterion(index, { description: event.target.value })} />
            </div>
            <Button type="button" variant="danger"
              onClick={() => setCriteria((current) => current.filter((_, criterionIndex) => criterionIndex !== index))}>
              {language === 'en' ? 'Remove criterion' : 'Usuń kryterium'}
            </Button>
          </div>)}
          <Button type="button" variant="ghost" disabled={criteria.length >= 20}
            onClick={() => setCriteria((current) => [...current, emptyCriterion()])}>
            {language === 'en' ? 'Add criterion' : 'Dodaj kryterium'}
          </Button>
        </fieldset>
        {submitError && <Alert variant="error">{submitError}</Alert>}
        {successMessage && <Alert>{successMessage}</Alert>}
        <Button type="submit" variant="ghost" disabled={isSubmitting}>
          {isSubmitting ? t.adding : editingTaskId
            ? (language === 'en' ? 'Save changes' : 'Zapisz zmiany')
            : t.addTask}
        </Button>
        {editingTaskId && <Button type="button" variant="ghost" onClick={cancelEditing}>
          {language === 'en' ? 'Cancel editing' : 'Anuluj edycję'}
        </Button>}
      </form>
    </section>
  )
}
