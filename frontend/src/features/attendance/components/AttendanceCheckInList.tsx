import { Button } from '../../../components/ui'
import { ResourceManager } from '../../resources/components/ResourceManager'
import { getAttendanceParticipants } from '../api/attendanceApi'
import type { AttendanceParticipant } from '../types'
import { AttendancePagedList } from './AttendancePagedList'
import { AttendanceTeamGroup } from './AttendanceTeamGroup'

function ParticipantGroups({
  hackathonPublicId,
  participants,
}: {
  hackathonPublicId: string
  participants: AttendanceParticipant[]
}) {
  const groups = new Map<string, { name: string; participants: AttendanceParticipant[] }>()
  for (const participant of participants) {
    const id = participant.team?.public_id ?? 'without-team'
    const group = groups.get(id) ?? { name: participant.team?.name ?? 'Bez drużyny', participants: [] }
    group.participants.push(participant)
    groups.set(id, group)
  }
  return (
    <div className="attendance-team-list">
      {[...groups.entries()].sort(([, a], [, b]) => a.name.localeCompare(b.name, 'pl'))
        .map(([id, group]) => (
          <AttendanceTeamGroup
            key={id}
            {...group}
            hackathonPublicId={hackathonPublicId}
          />
        ))}
    </div>
  )
}

export function AttendanceCheckInList({ hackathonPublicId }: { hackathonPublicId: string }) {
  return (
    <section className="attendance-participants" aria-label="Lista uczestników">
      <div className="attendance-participants-actions">
        <Button type="button" variant="ghost" disabled
          title="Wyśle zasoby wyłącznie uczestnikom z potwierdzoną obecnością; wymaga podłączenia backendu zasobów. Akcja obejmie wszystkich obecnych, niezależnie od strony.">
          Wyślij obecnym
        </Button>
      </div>
      <ResourceManager hackathonPublicId={hackathonPublicId} />
      <p>Grupowanie dotyczy bieżącej strony uczestników. Pełne składy znajdziesz w widoku „Drużyny”.</p>
      <AttendancePagedList hackathonPublicId={hackathonPublicId} loadPage={getAttendanceParticipants}
        label="Lista uczestników" emptyMessage="Brak zaakceptowanych uczestników.">
        {(items) => (
          <ParticipantGroups
            hackathonPublicId={hackathonPublicId}
            participants={items}
          />
        )}
      </AttendancePagedList>
    </section>
  )
}
