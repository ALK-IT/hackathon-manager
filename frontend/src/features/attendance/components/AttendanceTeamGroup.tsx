import { ResourceAssignmentControls } from '../../resources/components/ResourceAssignmentControls'
import type { AttendanceParticipant } from '../types'
import { AttendancePresenceStatus } from './AttendancePresenceStatus'

interface AttendanceTeamGroupProps {
  name: string
  participants: AttendanceParticipant[]
  hackathonPublicId: string
}

export function AttendanceTeamGroup({
  name,
  participants,
  hackathonPublicId,
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
            <ResourceAssignmentControls hackathonPublicId={hackathonPublicId} registrationPublicId={item.registration_public_id} />
          </li>
        ))}
      </ul>
    </section>
  )
}
