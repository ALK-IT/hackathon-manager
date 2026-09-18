import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, Card, Spinner } from '../../../components/ui'
import { AttendanceQrScanner } from '../../attendance'
import { isHackathonInProgress } from '../../hackathons/utils/hackathonTime'
import { getParticipantArea } from '../api/registrationApi'
import { ParticipantTaskCard } from '../components/ParticipantTaskCard'
import type { ParticipantArea } from '../types'
import { getParticipantAreaErrorMessage } from '../utils/registrationMessages'
import { useTranslation } from '../../../i18n/useTranslation'

export function ParticipantAreaPage() {
  const { language, t } = useTranslation()
  const { hackathonPublicId } = useParams()
  const [participantArea, setParticipantArea] = useState<ParticipantArea | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [loadError, setLoadError] = useState<string | null>(null)
  const [loadedAt] = useState(() => Date.now())

  useEffect(() => {
    const controller = new AbortController()

    async function loadParticipantArea() {
      if (!hackathonPublicId) {
        setLoadError(language === 'en' ? 'Invalid hackathon address.' : 'Nieprawidłowy adres hackathonu.')
        setIsLoading(false)
        return
      }

      try {
        setParticipantArea(
          await getParticipantArea(hackathonPublicId, controller.signal),
        )
      } catch (error) {
        if (error instanceof Error && error.name === 'AbortError') return
        setLoadError(getParticipantAreaErrorMessage(error, language))
      } finally {
        if (!controller.signal.aborted) setIsLoading(false)
      }
    }

    void loadParticipantArea()
    return () => controller.abort()
  }, [hackathonPublicId, language])

  return (
    <main className="app-page">
      <div className="details-back-link">
        <Link to="/hackathons">{t.backToList}</Link>
      </div>

      {isLoading && <Spinner label={t.loadingParticipantArea} />}
      {loadError && <Alert variant="error">{loadError}</Alert>}

      {participantArea && (
        <div className="participant-area-stack">
          <Card className="participant-area-card">
            <h1>{participantArea.name}</h1>
            <p>{participantArea.description}</p>
            {participantArea.team ? (
              <section aria-labelledby="participant-team-heading">
                <h2 id="participant-team-heading">{language === 'en' ? 'Team' : 'Drużyna'}: {participantArea.team.name}</h2>
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

          {isHackathonInProgress(
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
                    submissionsClosed={loadedAt >= Date.parse(participantArea.end_date)}
                  />
                ))}
              </div>
            ) : (
              <p>{t.noPublishedTasks}</p>
            )}
          </section>
        </div>
      )}
    </main>
  )
}
