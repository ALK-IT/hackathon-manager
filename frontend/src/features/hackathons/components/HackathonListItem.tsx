import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Countdown } from '../../../components/ui'
import type { Hackathon } from '../types'
import { getDeleteHackathonErrorMessage } from '../utils/hackathonMessages'

interface HackathonListItemProps {
  hackathon: Hackathon
  onDelete?: (hackathon: Hackathon) => Promise<void>
}

const registrationStatusLabels = {
  pending: 'oczekujące',
  accepted: 'zaakceptowane',
  rejected: 'odrzucone',
} as const

export function HackathonListItem({ hackathon, onDelete }: HackathonListItemProps) {
  const navigate = useNavigate()
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  async function handleDelete() {
    if (!window.confirm('Czy na pewno chcesz usunąć ten hackathon?')) return

    const confirmedName = window.prompt(
      `Aby potwierdzić usunięcie, wpisz nazwę hackathonu: ${hackathon.name}`,
    )
    if (confirmedName === null) return
    if (confirmedName.trim() !== hackathon.name) {
      setDeleteError('Wpisana nazwa nie jest zgodna z nazwą hackathonu.')
      return
    }

    setDeleteError(null)
    setIsDeleting(true)
    try {
      await onDelete?.(hackathon)
    } catch (error) {
      setDeleteError(getDeleteHackathonErrorMessage(error))
    } finally {
      setIsDeleting(false)
    }
  }

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
        {deleteError && <Alert variant="error">{deleteError}</Alert>}
        {hackathon.access_level === 'owner' && onDelete && (
          <Button
            type="button"
            variant="danger"
            disabled={isDeleting}
            onClick={() => void handleDelete()}
          >
            {isDeleting ? 'Usuwanie…' : 'Usuń hackathon'}
          </Button>
        )}
      </Card>
    </li>
  )
}
