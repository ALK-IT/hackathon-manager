import { Link, useNavigate } from 'react-router-dom'
import { Button, Card, Countdown } from '../../../components/ui'
import { getTranslations } from '../../../i18n/useTranslation'
import type { Language } from '../../auth'
import type { Hackathon } from '../types'

interface HackathonListItemProps {
  hackathon: Hackathon
  language?: Language
}

export function HackathonListItem({ hackathon, language = 'pl' }: HackathonListItemProps) {
  const navigate = useNavigate()
  const t = getTranslations(language)
  const registrationStatusLabels = {
    pending: t.pending,
    accepted: t.accepted,
    rejected: t.rejected,
  }

  return (
    <li>
      <Card>
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
              navigate(`/hackathons/${hackathon.public_id}/participant-area`)
            }
          >
            {t.enterHackathon}
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
      </Card>
    </li>
  )
}
