import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Button, Card, Countdown } from '../../../components/ui'
import { WithdrawRegistrationButton } from '../../registration/components/WithdrawRegistrationButton'
import type { Hackathon } from '../types'

interface HackathonListItemProps {
  hackathon: Hackathon
  onWithdraw?: (hackathon: Hackathon) => Promise<void>
}

const registrationStatusLabels = {
  pending: 'oczekujące',
  accepted: 'zaakceptowane',
  rejected: 'odrzucone',
} as const

export function HackathonListItem({ hackathon, onWithdraw }: HackathonListItemProps) {
  const navigate = useNavigate()
  const [renderedAt] = useState(() => Date.now())
  const canWithdraw = renderedAt < Date.parse(hackathon.end_date)

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
        {canWithdraw && hackathon.my_registration_status !== null && onWithdraw && (
          <WithdrawRegistrationButton onWithdraw={() => onWithdraw(hackathon)} />
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
      </Card>
    </li>
  )
}
