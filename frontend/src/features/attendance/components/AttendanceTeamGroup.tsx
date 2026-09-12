import { Button } from '../../../components/ui'
import type { AttendanceParticipant } from '../types'
import { AttendancePresenceStatus } from './AttendancePresenceStatus'

interface AttendanceTeamGroupProps {
  name: string
  participants: AttendanceParticipant[]
  selectedResourceName: string | null
  assignedRegistrationIds: Set<string>
  pendingRegistrationIds: Set<string>
  hasAvailableItems: boolean
  onAssign: (registrationPublicId: string) => void
  onRevoke: (registrationPublicId: string) => void
}

export function AttendanceTeamGroup({
  name,
  participants,
  selectedResourceName,
  assignedRegistrationIds,
  pendingRegistrationIds,
  hasAvailableItems,
  onAssign,
  onRevoke,
}: AttendanceTeamGroupProps) {
  return (
    <section className="attendance-team-group" aria-label={`Drużyna ${name}`}>
      <h2>{name}</h2>
      <ul className="attendance-participants-list">
        {participants.map((item) => {
          const registrationPublicId = item.registration_public_id
          const isAssigned = assignedRegistrationIds.has(registrationPublicId)
          const isPending = pendingRegistrationIds.has(registrationPublicId)

          return (
            <li key={registrationPublicId}>
              <div className="attendance-participant-details">
                <strong>{item.participant.name}</strong>
                <span>{item.participant.email}</span>
                <AttendancePresenceStatus isPresent={item.is_present} />
                {selectedResourceName && (
                  <span className="attendance-resource-status">
                    {isAssigned
                      ? `Przydzielono: ${selectedResourceName}`
                      : `Nie przydzielono: ${selectedResourceName}`}
                  </span>
                )}
              </div>
              <div className="attendance-resource-actions">
                <Button
                  type="button"
                  variant="ghost"
                  disabled={
                    selectedResourceName === null ||
                    isAssigned ||
                    isPending ||
                    !hasAvailableItems
                  }
                  onClick={() => onAssign(registrationPublicId)}
                >
                  {isPending && !isAssigned ? 'Dodawanie…' : 'Dodaj zasoby'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  disabled={
                    selectedResourceName === null || !isAssigned || isPending
                  }
                  onClick={() => onRevoke(registrationPublicId)}
                >
                  {isPending && isAssigned ? 'Cofanie…' : 'Cofnij zasoby'}
                </Button>
              </div>
            </li>
          )
        })}
      </ul>
    </section>
  )
}
