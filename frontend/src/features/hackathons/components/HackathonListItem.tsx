import { Link, useNavigate } from 'react-router-dom'
import { Button, Card } from '../../../components/ui'
import type { Hackathon } from '../types'

interface HackathonListItemProps {
  hackathon: Hackathon
}

const registrationStatusLabels = {
  pending: 'oczekujące',
  accepted: 'zaakceptowane',
  rejected: 'odrzucone',
} as const

export function HackathonListItem({ hackathon }: HackathonListItemProps) {
  const navigate = useNavigate()

  return (
    <li>
      <Card>
        <h3>
          <Link to={`/hackathons/${hackathon.public_id}`}>{hackathon.name}</Link>
        </h3>
        <p>
          {new Date(hackathon.start_date).toLocaleDateString('pl-PL')} –{' '}
          {new Date(hackathon.end_date).toLocaleDateString('pl-PL')}
        </p>
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
        {hackathon.access_level !== 'viewer' && (
          <Button
            type="button"
            onClick={() => navigate(`/hackathons/${hackathon.public_id}/settings`)}
          >
            Ustawienia
          </Button>
        )}
      </Card>
    </li>
  )
}
