import { Link, useParams } from 'react-router-dom'
import { Alert, Card } from '../../../components/ui'
import { AttendanceCheckInList } from '../components/AttendanceCheckInList'

export function AttendanceParticipantsPage() {
  const { hackathonPublicId } = useParams()

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
          <AttendanceCheckInList hackathonPublicId={hackathonPublicId} />
        ) : (
          <Alert variant="error">Nieprawidłowy adres hackathonu.</Alert>
        )}
      </Card>
    </main>
  )
}
