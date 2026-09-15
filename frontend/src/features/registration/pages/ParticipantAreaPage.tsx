import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { ParticipantResults } from '../../evaluations/components/ParticipantResults'
import { useHasEnded } from '../../evaluations/utils'
import { AttendanceQrScanner } from '../../attendance'
import { isHackathonInProgress } from '../../hackathons/utils/hackathonTime'
import { getParticipantArea } from '../api/registrationApi'
import { ParticipantTaskCard } from '../components/ParticipantTaskCard'
import type { ParticipantArea } from '../types'
import { getParticipantAreaErrorMessage } from '../utils/registrationMessages'

export function ParticipantAreaPage() {
  const { hackathonPublicId } = useParams()
  const [params, setParams] = useSearchParams()
  const resultsRequested = params.get('view') === 'results'
  const [refresh, setRefresh] = useState(0)
  const [participantArea, setParticipantArea] = useState<ParticipantArea | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loadedAt] = useState(() => Date.now())
  const hasEnded = useHasEnded(participantArea?.end_date ?? '')

  useEffect(() => {
    const controller = new AbortController()
    setParticipantArea(null)
    setIsLoading(true)
    setLoadError(null)

    async function loadParticipantArea() {
      if (!hackathonPublicId) {
        setLoadError('Nieprawidłowy adres hackathonu.')
        setIsLoading(false)
        return
      }

      try {
        const data = await getParticipantArea(hackathonPublicId, controller.signal)
        if (!controller.signal.aborted) setParticipantArea(data)
      } catch (error) {
        if (controller.signal.aborted) return
        setLoadError(getParticipantAreaErrorMessage(error))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadParticipantArea()
    return () => controller.abort()
  }, [hackathonPublicId, resultsRequested, refresh])

  return (
    <main className="app-page">
      <div className="details-back-link">
        <Link to="/hackathons">Wróć do listy hackathonów</Link>
      </div>

      {isLoading && <Spinner label="Ładowanie strefy uczestnika…" />}
      {loadError && <Alert variant="error">{loadError}</Alert>}
      {loadError && <Button variant="ghost" onClick={() => setRefresh((value) => value + 1)}>Spróbuj ponownie</Button>}

      {participantArea && (
        <div className="participant-area-stack">
          <Card className="participant-area-card">
            <h1>{participantArea.name}</h1>
            <p>{participantArea.description}</p>
            {participantArea.team ? (
              <section aria-labelledby="participant-team-heading">
                <h2 id="participant-team-heading">Drużyna: {participantArea.team.name}</h2>
                <h3>Członkowie</h3>
                <ul className="participant-list">
                  {participantArea.team.members.map((member) => (
                    <li key={member.public_id}>{member.name}</li>
                  ))}
                </ul>
              </section>
            ) : (
              <p>Nie należysz do żadnej drużyny.</p>
            )}
          </Card>

          {hasEnded && <nav aria-label="Widok uczestnika">
            <Button variant="ghost" onClick={() => setParams({})}>Zadania</Button>
            <Button variant="ghost" onClick={() => setParams({ view: 'results' })}>Zobacz wyniki</Button>
            {resultsRequested && <Button variant="ghost" onClick={() => setRefresh((value) => value + 1)}>Odśwież wyniki</Button>}
          </nav>}

          {!hasEnded && isHackathonInProgress(
            participantArea.start_date,
            participantArea.end_date,
            loadedAt,
          ) && (
            <Card>
              <AttendanceQrScanner
                hackathonPublicId={participantArea.public_id}
              />
            </Card>
          )}

          {hasEnded && resultsRequested ? <ParticipantResults tasks={participantArea.tasks} /> : <section aria-labelledby="participant-tasks-heading">
            <h2 id="participant-tasks-heading">Zadania</h2>
            {participantArea.tasks.length > 0 ? (
              <div className="participant-task-list">
                {participantArea.tasks.map((task) => (
                  <ParticipantTaskCard
                    key={task.public_id}
                    hackathonPublicId={participantArea.public_id}
                    task={task}
                    canSubmit={participantArea.team !== null}
                    submissionsClosed={hasEnded}
                  />
                ))}
              </div>
            ) : (
              <p>Nie opublikowano jeszcze żadnych zadań.</p>
            )}
          </section>}
        </div>
      )}
    </main>
  )
}
