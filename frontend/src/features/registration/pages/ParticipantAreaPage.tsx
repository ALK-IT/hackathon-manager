import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { HackathonResourcesPanel } from '../../resources/components/HackathonResourcesPanel'
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
  const [activeTab, setActiveTab] = useState<'hackathon' | 'resources'>('hackathon')

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
          <div className="participant-area-tabs" role="tablist" aria-label="Widok hackathonu">
            <Button
              type="button"
              role="tab"
              variant="ghost"
              aria-selected={activeTab === 'hackathon'}
              aria-controls="participant-hackathon-panel"
              onClick={() => setActiveTab('hackathon')}
            >
              Hackathon
            </Button>
            <Button
              type="button"
              role="tab"
              variant="ghost"
              aria-selected={activeTab === 'resources'}
              aria-controls="participant-resources-panel"
              onClick={() => setActiveTab('resources')}
            >
              Moje zasoby
            </Button>
          </div>

          {activeTab === 'hackathon' && (
            <div id="participant-hackathon-panel" role="tabpanel">
              <div className="participant-area-stack">
                <Card className="participant-area-card">
                  <h1>{participantArea.name}</h1>
                  <p>{participantArea.description}</p>
                  {participantArea.team ? (
                    <section aria-labelledby="participant-team-heading">
                      <h2 id="participant-team-heading">
                        Drużyna: {participantArea.team.name}
                      </h2>
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
                          submissionsClosed={
                            loadedAt >= Date.parse(participantArea.end_date)
                          }
                        />
                      ))}
                    </div>
                  ) : (
                    <p>Nie opublikowano jeszcze żadnych zadań.</p>
                  )}
                </section>
              </div>
            </div>
          )}

          {activeTab === 'resources' && (
            <div id="participant-resources-panel" role="tabpanel">
              <HackathonResourcesPanel
                hackathonPublicId={participantArea.public_id}
              />
            </div>
          )}
        </div>
      )}
    </main>
  )
}
