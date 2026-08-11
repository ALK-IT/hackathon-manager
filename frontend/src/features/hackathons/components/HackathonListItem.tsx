import { Card } from '../../../components/ui'
import type { Hackathon } from '../types'

interface HackathonListItemProps {
  hackathon: Hackathon
}

export function HackathonListItem({ hackathon }: HackathonListItemProps) {
  return (
    <li>
      <Card>
        <h3>{hackathon.name}</h3>
        <p>
          {new Date(hackathon.start_date).toLocaleDateString('pl-PL')} –{' '}
          {new Date(hackathon.end_date).toLocaleDateString('pl-PL')}
        </p>
        <p>Rejestracja: {hackathon.registration_open ? 'otwarta' : 'zamknięta'}</p>
      </Card>
    </li>
  )
}
