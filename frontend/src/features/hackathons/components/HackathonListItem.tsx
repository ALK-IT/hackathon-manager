import { Link, useNavigate } from 'react-router-dom'
import { Button, Card, Countdown } from '../../../components/ui'
import type { Hackathon } from '../types'
import { AttendanceSummaryPanel } from '../../attendance/components/AttendanceSummaryPanel'

interface HackathonListItemProps {
  hackathon: Hackathon
  isAdmin?: boolean
}

const registrationStatusLabels = {
  pending: 'oczekujące',
  accepted: 'zaakceptowane',
  rejected: 'odrzucone',
} as const

export function HackathonListItem({ hackathon, isAdmin = false }: HackathonListItemProps) {
  const navigate = useNavigate()
  const canSeeSummary = isAdmin || hackathon.access_level === 'owner' ||
    hackathon.access_level === 'co_organizer'

  return (
    <li>
      <Card className={canSeeSummary ? 'hackathon-card-with-summary' : undefined}>
        <div>
        <h3>
          <Link to={`/hackathons/${hackathon.public_id}`}>{hackathon.name}</Link>
        </h3>
        <p>
          {new Date(hackathon.start_date).toLocaleDateString('pl-PL')} –{' '}
          {new Date(hackathon.end_date).toLocaleDateString('pl-PL')}
        </p>
        <Countdown startDate={hackathon.start_date} endDate={hackathon.end_date} />
        <p>Rejestracja: {hackathon.registration_open ? 'otwarta' : 'zamknięta'}</p>
        {hackathon.my_registration_status && (
          <p>
            Status zgłoszenia:{' '}
            {registrationStatusLabels[hackathon.my_registration_status]}
          </p>
        )}
        {hackathon.my_registration_status === 'accepted' ? (
          <Button
            type="button"
            variant="ghost"
            onClick={() =>
              navigate(`/hackathons/${hackathon.public_id}/participant-area`)
            }
          >
            Przejdź do hackathonu
          </Button>
        ) : (
          hackathon.my_registration_status === null &&
          hackathon.registration_open && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate(`/hackathons/${hackathon.public_id}/register`)}
            >
              Zarejestruj się
            </Button>
          )
        )}
        {(hackathon.access_level === 'owner' ||
          hackathon.access_level === 'co_organizer') && (
          <>
            <Button
              type="button"
              onClick={() => navigate(`/hackathons/${hackathon.public_id}/registrations`)}
            >
              Zgłoszenia
            </Button>
            <Button
              type="button"
              onClick={() => navigate(`/hackathons/${hackathon.public_id}/settings`)}
            >
              Ustawienia
            </Button>
          </>
        )}
        </div>
        {canSeeSummary && (
          <aside className="hackathon-card-summary" aria-label={`Podsumowanie: ${hackathon.name}`}>
            <AttendanceSummaryPanel hackathonPublicId={hackathon.public_id} />
          </aside>
        )}
      </Card>
    </li>
  )
}
