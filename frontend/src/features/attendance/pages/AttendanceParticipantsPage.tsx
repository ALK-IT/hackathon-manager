import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { Alert, Button, Card } from '../../../components/ui'
import { AttendanceCheckInList } from '../components/AttendanceCheckInList'
import { AttendanceSummaryPanel } from '../components/AttendanceSummaryPanel'
import { AttendanceTeamsList } from '../components/AttendanceTeamsList'

export function AttendanceParticipantsPage() {
  const { hackathonPublicId } = useParams()
  const [view, setView] = useState<'participants' | 'teams'>('participants')

  return (
    <main className="app-page">
      <div className="details-back-link">
        <Link to={`/hackathons/${hackathonPublicId ?? ''}`}>
          Wróć do hackathonu
        </Link>
      </div>

      <Card>
        <h1>Uczestnicy</h1>
        {hackathonPublicId && <Link to={`/hackathons/${hackathonPublicId}/solutions`}>Sprawdź rozwiązania</Link>}
        <p>
          Lista zaakceptowanych uczestników. Osoby, które zeskanowały kod QR,
          są oznaczone jako obecne.
        </p>
        {hackathonPublicId ? (
          <>
            <AttendanceSummaryPanel hackathonPublicId={hackathonPublicId} />
            <nav aria-label="Widok listy">
              <Button type="button" variant="ghost" aria-pressed={view === 'participants'}
                onClick={() => setView('participants')}>Uczestnicy</Button>
              <Button type="button" variant="ghost" aria-pressed={view === 'teams'}
                onClick={() => setView('teams')}>Drużyny</Button>
            </nav>
            {view === 'participants' ? <AttendanceCheckInList hackathonPublicId={hackathonPublicId} />
              : <AttendanceTeamsList hackathonPublicId={hackathonPublicId} />}
          </>
        ) : (
          <Alert variant="error">Nieprawidłowy adres hackathonu.</Alert>
        )}
      </Card>
    </main>
  )
}
