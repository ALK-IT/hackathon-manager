import { Button } from '../../../components/ui'
import type { AttendanceParticipant } from '../types'
import { AttendancePresenceStatus } from './AttendancePresenceStatus'

interface AttendanceTeamGroupProps {
  name: string
  participants: AttendanceParticipant[]
}

export function AttendanceTeamGroup({
  name,
  participants,
}: AttendanceTeamGroupProps) {
  return (
    <section className="attendance-team-group" aria-label={`Drużyna ${name}`}>
      <h2>{name}</h2>
      <ul className="attendance-participants-list">
        {participants.map((item) => (
          <li key={item.registration_public_id}>
            <div className="attendance-participant-details">
              <strong>{item.participant.name}</strong>
              <span>{item.participant.email}</span>
              <AttendancePresenceStatus isPresent={item.is_present} />
            </div>
            <div className="attendance-resource-actions">
              <Button
                type="button"
                variant="ghost"
                disabled
                title="Wymaga podłączenia backendu zasobów"
              >
                Dodaj zasoby
              </Button>
              <Button
                type="button"
                variant="ghost"
                disabled
                title="Wymaga podłączenia backendu zasobów"
              >
                Cofnij zasoby
              </Button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
