import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { Alert, Button, Card, Countdown } from '../../../components/ui'
import { getTranslations } from '../../../i18n/useTranslation'
import type { Language } from '../../auth'
import { WithdrawRegistrationButton } from '../../registration/components/WithdrawRegistrationButton'
import type { Hackathon } from '../types'
import { useHasEnded } from '../../evaluations/utils'
import { AttendanceSummaryPanel } from '../../attendance/components/AttendanceSummaryPanel'
import { getDeleteHackathonErrorMessage } from '../utils/hackathonMessages'

interface HackathonListItemProps {
  hackathon: Hackathon
  isAdmin?: boolean
  language?: Language
  onWithdraw?: (hackathon: Hackathon) => Promise<void>
  onDelete?: (hackathon: Hackathon) => Promise<void>
}

export function HackathonListItem({
  hackathon,
  isAdmin = false,
  language = 'pl',
  onWithdraw,
  onDelete,
}: HackathonListItemProps) {
  const navigate = useNavigate()
  const hasEnded = useHasEnded(hackathon.end_date)
  const canSeeSummary = isAdmin || hackathon.access_level === 'owner' ||
    hackathon.access_level === 'co_organizer'
  const t = getTranslations(language)
  const registrationStatusLabels = {
    pending: t.pending,
    accepted: t.accepted,
    rejected: t.rejected,
  }
  const [renderedAt] = useState(() => Date.now())
  const canWithdraw = renderedAt < Date.parse(hackathon.end_date)
  const [isDeleting, setIsDeleting] = useState(false)
  const [deleteError, setDeleteError] = useState<string | null>(null)

  async function handleDelete() {
    const confirmMessage = language === 'en'
      ? 'Are you sure you want to delete this hackathon?'
      : 'Czy na pewno chcesz usunąć ten hackathon?'
    if (!window.confirm(confirmMessage)) return

    const confirmedName = window.prompt(
      language === 'en'
        ? `To confirm deletion, enter the hackathon name: ${hackathon.name}`
        : `Aby potwierdzić usunięcie, wpisz nazwę hackathonu: ${hackathon.name}`,
    )
    if (confirmedName === null) return
    if (confirmedName.trim() !== hackathon.name) {
      setDeleteError(language === 'en'
        ? 'The entered name does not match the hackathon name.'
        : 'Wpisana nazwa nie jest zgodna z nazwą hackathonu.')
      return
    }

    setDeleteError(null)
    setIsDeleting(true)
    try {
      await onDelete?.(hackathon)
    } catch (error) {
      setDeleteError(getDeleteHackathonErrorMessage(error, language))
    } finally {
      setIsDeleting(false)
    }
  }

  return (
    <li>
      <Card className={canSeeSummary ? 'hackathon-card-with-summary' : undefined}>
        <div>
        <h3>
          <Link to={`/hackathons/${hackathon.public_id}`}>{hackathon.name}</Link>
        </h3>
        <p>
          {new Date(hackathon.start_date).toLocaleDateString(language === 'pl' ? 'pl-PL' : 'en-US')} –{' '}
          {new Date(hackathon.end_date).toLocaleDateString(language === 'pl' ? 'pl-PL' : 'en-US')}
        </p>
        <Countdown startDate={hackathon.start_date} endDate={hackathon.end_date} language={language} />
        <p>{t.registrationLabel}: {hackathon.registration_open ? t.registrationOpen : t.registrationClosed}</p>
        {hackathon.my_registration_status && (
          <p>
            {t.applicationStatus}:{' '}
            {registrationStatusLabels[hackathon.my_registration_status]}
          </p>
        )}
        {hackathon.my_registration_status === 'accepted' ? (
          <Button
            type="button"
            variant="ghost"
            onClick={() =>
              navigate(`/hackathons/${hackathon.public_id}/participant-area${hasEnded ? '?view=results' : ''}`)
            }
          >
            {hasEnded
              ? (language === 'en' ? 'View results' : 'Zobacz wyniki')
              : t.enterHackathon}
          </Button>
        ) : (
          hackathon.my_registration_status === null &&
          hackathon.registration_open && (
            <Button
              type="button"
              variant="ghost"
              onClick={() => navigate(`/hackathons/${hackathon.public_id}/register`)}
            >
              {t.register}
            </Button>
          )
        )}
        {canWithdraw && hackathon.my_registration_status !== null && onWithdraw && (
          <WithdrawRegistrationButton language={language} onWithdraw={() => onWithdraw(hackathon)} />
        )}
        {(hackathon.access_level === 'owner' ||
          hackathon.access_level === 'co_organizer') && (
          <>
            <Button
              type="button"
              onClick={() => navigate(`/hackathons/${hackathon.public_id}/registrations`)}
            >
              {t.applications}
            </Button>
            <Button
              type="button"
              onClick={() => navigate(`/hackathons/${hackathon.public_id}/settings`)}
            >
              {t.settings}
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
            {isDeleting
              ? (language === 'en' ? 'Deleting…' : 'Usuwanie…')
              : (language === 'en' ? 'Delete hackathon' : 'Usuń hackathon')}
          </Button>
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
