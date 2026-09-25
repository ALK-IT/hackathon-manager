import { useState } from 'react'
import { Link, useParams, useSearchParams } from 'react-router-dom'
import { Alert, Button, Card } from '../../../components/ui'
import { ResourceManager } from '../../resources/components/ResourceManager'
import { SubmissionReviewPanel } from '../../evaluations/pages/SubmissionReviewPage'
import { AttendanceCheckInList } from '../components/AttendanceCheckInList'
import { AttendanceSummaryPanel } from '../components/AttendanceSummaryPanel'
import { AttendanceTeamsList } from '../components/AttendanceTeamsList'

export function AttendanceParticipantsPage() {
  const { hackathonPublicId } = useParams()
  const [params] = useSearchParams()
  const [view, setView] = useState<'summary' | 'participants' | 'teams' | 'resources' | 'solutions'>(
    params.get('view') === 'solutions' ? 'solutions' : 'participants',
  )

  return (
    <main className="app-page">
      <div className="details-back-link">
        <Link to={`/hackathons/${hackathonPublicId ?? ''}`}>
          Wróć do hackathonu
        </Link>
      </div>

      <Card>
        <h1>Uczestnicy</h1>
        <p>
          Lista zaakceptowanych uczestników. Osoby, które zeskanowały kod QR,
          są oznaczone jako obecne.
        </p>
        {hackathonPublicId ? (
          <>
            <div className="attendance-tabs" role="tablist" aria-label="Sekcje zarządzania uczestnikami">
              <Button type="button" role="tab" variant="ghost"
                aria-selected={view === 'summary'} aria-controls="attendance-summary-panel"
                onClick={() => setView('summary')}>Podsumowanie</Button>
              <Button type="button" role="tab" variant="ghost"
                aria-selected={view === 'participants'} aria-controls="attendance-participants-panel"
                onClick={() => setView('participants')}>Uczestnicy</Button>
              <Button type="button" role="tab" variant="ghost"
                aria-selected={view === 'teams'} aria-controls="attendance-teams-panel"
                onClick={() => setView('teams')}>Drużyny</Button>
              <Button type="button" role="tab" variant="ghost"
                aria-selected={view === 'resources'} aria-controls="attendance-resources-panel"
                onClick={() => setView('resources')}>Zasoby</Button>
              <Button type="button" role="tab" variant="ghost"
                aria-selected={view === 'solutions'} aria-controls="attendance-solutions-panel"
                onClick={() => setView('solutions')}>Rozwiązania</Button>
            </div>
            {view === 'summary' && <div id="attendance-summary-panel" role="tabpanel">
              <AttendanceSummaryPanel hackathonPublicId={hackathonPublicId} />
            </div>}
            {view === 'participants' && <div id="attendance-participants-panel" role="tabpanel">
              <AttendanceCheckInList hackathonPublicId={hackathonPublicId} />
            </div>}
            {view === 'teams' && <div id="attendance-teams-panel" role="tabpanel">
              <AttendanceTeamsList hackathonPublicId={hackathonPublicId} />
            </div>}
            {view === 'resources' && <div id="attendance-resources-panel" role="tabpanel">
              <ResourceManager hackathonPublicId={hackathonPublicId} />
            </div>}
            {view === 'solutions' && <div id="attendance-solutions-panel" role="tabpanel">
              <SubmissionReviewPanel hackathonPublicId={hackathonPublicId} />
            </div>}
          </>
        ) : (
          <Alert variant="error">Nieprawidłowy adres hackathonu.</Alert>
        )}
      </Card>
    </main>
  )
}
