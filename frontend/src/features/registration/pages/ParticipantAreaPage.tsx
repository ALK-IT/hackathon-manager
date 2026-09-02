import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, Card, Spinner } from '../../../components/ui'
import { getParticipantArea } from '../api/registrationApi'
import { ParticipantTaskCard } from '../components/ParticipantTaskCard'
import type { ParticipantArea } from '../types'
import { getParticipantAreaErrorMessage } from '../utils/registrationMessages'

export function ParticipantAreaPage() {
  const { hackathonPublicId } = useParams()
  const [participantArea, setParticipantArea] = useState<ParticipantArea | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loadedAt] = useState(() => Date.now())

  useEffect(() => {
    const controller = new AbortController()

    async function loadParticipantArea() {
      if (!hackathonPublicId) {
        setLoadError('Nieprawidłowy adres hackathonu.')
        setIsLoading(false)
        return
      }

      try {
        setParticipantArea(
          await getParticipantArea(hackathonPublicId, controller.signal),
        )
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
        setLoadError(getParticipantAreaErrorMessage(error))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadParticipantArea()
    return () => controller.abort()
  }, [hackathonPublicId])

  return (
    <main className="app-page">
      <div className="details-back-link">
        <Link to="/hackathons">Wróć do listy hackathonów</Link>
      </div>

      {isLoading && <Spinner label="Ładowanie strefy uczestnika…" />}
      {loadError && <Alert variant="error">{loadError}</Alert>}

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

          <section aria-labelledby="participant-tasks-heading">
            <h2 id="participant-tasks-heading">Zadania</h2>
            {participantArea.tasks.length > 0 ? (
              <div className="participant-task-list">
                {participantArea.tasks.map((task) => (
                  <ParticipantTaskCard
                    key={task.public_id}
                    hackathonPublicId={participantArea.public_id}
                    task={task}
                    canSubmit={participantArea.team !== null}
                    submissionsClosed={loadedAt >= Date.parse(participantArea.end_date)}
                  />
                ))}
              </div>
            ) : loadedAt < Date.parse(participantArea.tasks_released_at) ? (
              <p>Zadania nie zostały jeszcze opublikowane.</p>
            ) : (
              <p>Nie dodano jeszcze żadnych zadań.</p>
            )}
          </section>
        </div>
      )}
    </main>
  )
}
