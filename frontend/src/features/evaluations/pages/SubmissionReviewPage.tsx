import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Alert, Button } from '../../../components/ui'
import { useAuth } from '../../auth'
import { getHackathon, getHackathonTasks } from '../../hackathons/api/hackathonsApi'
import type { HackathonDetails, HackathonTask } from '../../hackathons/types'
import { SubmissionList } from '../components/SubmissionList'
import { Leaderboard } from '../components/Leaderboard'
import { evaluationError, useHasEnded } from '../utils'

export function SubmissionReviewPage() {
  const { hackathonPublicId = '' } = useParams()
  return <Review key={hackathonPublicId} id={hackathonPublicId} embedded={false} />
}

export function SubmissionReviewPanel({ hackathonPublicId }: { hackathonPublicId: string }) {
  return <Review key={hackathonPublicId} id={hackathonPublicId} embedded />
}

function Review({ id, embedded }: { id: string; embedded: boolean }) {
  const { user, isLoading: authLoading } = useAuth()
  const [params, setParams] = useSearchParams()
  const [hackathon, setHackathon] = useState<HackathonDetails | null>(null)
  const [tasks, setTasks] = useState<HackathonTask[]>([])
  const [error, setError] = useState<string | null>(null)
  const [retry, setRetry] = useState(0)
  const [view, setView] = useState<'submissions' | 'leaderboard'>('submissions')
  const ended = useHasEnded(hackathon?.end_date ?? '')
  const canManage = user?.role === 'admin' || hackathon?.access_level === 'owner' ||
    hackathon?.access_level === 'co_organizer'

  useEffect(() => {
    if (authLoading) return
    const controller = new AbortController()
    setHackathon(null)
    setError(null)
    async function load() {
      try {
        const details = await getHackathon(id, controller.signal)
        if (controller.signal.aborted) return
        if (user?.role !== 'admin' && details.access_level !== 'owner' && details.access_level !== 'co_organizer') {
          setError('Nie masz uprawnień do przeglądania rozwiązań.')
          return
        }
        const taskList = await getHackathonTasks(id, controller.signal)
        if (controller.signal.aborted) return
        setTasks(taskList)
        setHackathon(details)
      } catch (cause) {
        if (!controller.signal.aborted) setError(evaluationError(cause))
      }
    }
    void load()
    return () => controller.abort()
  }, [id, authLoading, user?.role, retry])

  const teamId = params.get('team') || undefined
  const taskId = params.get('task') || undefined
  const state = params.get('evaluated') ?? ''
  const evaluated = state === 'true' ? true : state === 'false' ? false : undefined
  function filter(name: string, value: string) {
    const next = new URLSearchParams(params)
    if (value) next.set(name, value)
    else next.delete(name)
    setParams(next)
  }

  const content = <>
      {error ? <><Alert variant="error">{error}</Alert>
        <Button variant="ghost" onClick={() => setRetry((value) => value + 1)}>Spróbuj ponownie</Button></>
        : !hackathon && <p role="status">Ładowanie hackathonu…</p>}
      {hackathon && canManage && <>
        <p>{hackathon.name}</p>
        {!ended && <p>Ocenianie będzie dostępne po zakończeniu hackathonu.</p>}
        <div className="solutions-tabs" role="tablist" aria-label="Widok rozwiązań">
          <Button type="button" role="tab" variant="ghost" aria-selected={view === 'submissions'}
            onClick={() => setView('submissions')}>Rozwiązania drużyn</Button>
          <Button type="button" role="tab" variant="ghost" aria-selected={view === 'leaderboard'}
            onClick={() => setView('leaderboard')}>Leaderboard</Button>
        </div>
        {view === 'submissions' && <>
        {teamId && <p>Rozwiązania wybranej drużyny. <Button variant="ghost"
          onClick={() => filter('team', '')}>Pokaż wszystkie drużyny</Button></p>}
        <div className="submission-filters">
        <label>Zadanie <select value={taskId ?? ''} onChange={(event) => filter('task', event.target.value)}>
          <option value="">Wszystkie zadania</option>
          {tasks.map((task) => <option key={task.public_id} value={task.public_id}>{task.title}</option>)}
        </select></label>
        <label>Stan oceny <select value={state} onChange={(event) => filter('evaluated', event.target.value)}>
          <option value="">Wszystkie</option><option value="false">Nieocenione</option><option value="true">Ocenione</option>
        </select></label>
        </div>
        <SubmissionList key={`${id}:${teamId}:${taskId}:${evaluated}`} hackathonId={id}
          teamId={teamId} taskId={taskId} evaluated={evaluated} canEvaluate={ended} />
        </>}
        {view === 'leaderboard' && <Leaderboard hackathonId={id} canManage
          initiallyVisibleToParticipants={hackathon.leaderboard_visible_to_participants ?? false} />}
      </>}
  </>

  if (embedded) {
    return <section aria-label="Rozwiązania">
      <h2>{ended ? 'Oceń rozwiązania' : 'Zobacz rozwiązania'}</h2>
      {content}
    </section>
  }

  return (
    <main className="app-page">
      <Link to={`/hackathons/${id}/attendance`}>Wróć do uczestników</Link>
      <h1>{ended ? 'Oceń rozwiązania' : 'Zobacz rozwiązania'}</h1>
      {content}
    </main>
  )
}
