import { useNavigate } from 'react-router-dom'
import { Button, Card } from '../../../components/ui'
import type { Hackathon } from '../types'

interface HackathonListItemProps {
  hackathon: Hackathon
}

export function HackathonListItem({ hackathon }: HackathonListItemProps) {
  const navigate = useNavigate()

  return (
    <li>
      <Card>
        <h3>{hackathon.name}</h3>
        <p>
          {new Date(hackathon.start_date).toLocaleDateString('pl-PL')} –{' '}
          {new Date(hackathon.end_date).toLocaleDateString('pl-PL')}
        </p>
        <p>Rejestracja: {hackathon.registration_open ? 'otwarta' : 'zamknięta'}</p>
        {hackathon.registration_open && (
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate(`/hackathons/${hackathon.public_id}/register`)}
          >
            Zarejestruj się
          </Button>
        )}
        {hackathon.access_level !== 'viewer' && (
          <Button
            type="button"
            variant="ghost"
            onClick={() => navigate(`/hackathons/${hackathon.public_id}/settings`)}
          >
            Ustawienia
          </Button>
        )}
      </Card>
    </li>
  )
}
