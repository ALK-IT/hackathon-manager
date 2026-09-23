import { useEffect, useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { ParticipantResults } from '../../evaluations/components/ParticipantResults'
import { useHasEnded } from '../../evaluations/utils'
import { AttendanceQrScanner } from '../../attendance'
import { isHackathonInProgress } from '../../hackathons/utils/hackathonTime'
import { Alert, Button, Card, Spinner } from '../../../components/ui'
import { HackathonResourcesPanel } from '../../resources/components/HackathonResourcesPanel'
import { getParticipantArea } from '../api/registrationApi'
import { ParticipantTaskCard } from '../components/ParticipantTaskCard'
import type { ParticipantArea } from '../types'
import { getParticipantAreaErrorMessage } from '../utils/registrationMessages'
import { useTranslation } from '../../../i18n/useTranslation'

export function ParticipantAreaPage() {
  const { language, t } = useTranslation()
  const { hackathonPublicId } = useParams()
  const [params, setParams] = useSearchParams()
  const resultsRequested = params.get('view') === 'results'
  const [refresh, setRefresh] = useState(0)
  const [participantArea, setParticipantArea] = useState<ParticipantArea | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loadedAt] = useState(() => Date.now())
  const [activeTab, setActiveTab] = useState<'hackathon' | 'resources'>('hackathon')
  const hasEnded = useHasEnded(participantArea?.end_date ?? '')

  useEffect(() => {
    const controller = new AbortController()
    setParticipantArea(null)
    setIsLoading(true)
    setLoadError(null)

    async function loadParticipantArea() {
      if (!hackathonPublicId) {
        setLoadError(language === 'en' ? 'Invalid hackathon address.' : 'Nieprawidłowy adres hackathonu.')
        setIsLoading(false)
        return
      }

      try {
        const data = await getParticipantArea(hackathonPublicId, controller.signal)
        if (!controller.signal.aborted) setParticipantArea(data)
      } catch (error) {
        if (controller.signal.aborted || (error instanceof Error && error.name === 'AbortError')) return
        setLoadError(getParticipantAreaErrorMessage(error, language))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadParticipantArea()
    return () => controller.abort()
  }, [hackathonPublicId, language, refresh, resultsRequested])

  return (
    <main className="app-page">
      <div className="details-back-link">
        <Link to="/hackathons">{t.backToList}</Link>
      </div>

      {isLoading && <Spinner label={t.loadingParticipantArea} />}
      {loadError && <Alert variant="error">{loadError}</Alert>}
      {loadError && <Button variant="ghost" onClick={() => setRefresh((value) => value + 1)}>Spróbuj ponownie</Button>}

      {participantArea && (
        <div className="participant-area-stack">
          <div className="participant-area-tabs" role="tablist" aria-label={language === 'en' ? 'Hackathon view' : 'Widok hackathonu'}>
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
              {language === 'en' ? 'My resources' : 'Moje zasoby'}
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
                        {language === 'en' ? 'Team' : 'Drużyna'}: {participantArea.team.name}
                      </h2>
                      <h3>{t.members}</h3>
                      <ul className="participant-list">
                        {participantArea.team.members.map((member) => (
                          <li key={member.public_id}>{member.name}</li>
                        ))}
                      </ul>
                    </section>
                  ) : (
                    <p>{t.noTeam}</p>
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

                {hasEnded && resultsRequested ? (
                  <ParticipantResults tasks={participantArea.tasks} />
                ) : (
                  <section aria-labelledby="participant-tasks-heading">
                    <h2 id="participant-tasks-heading">{t.tasks}</h2>
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
                    <p>{t.noPublishedTasks}</p>
                  )}
                  </section>
                )}
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
