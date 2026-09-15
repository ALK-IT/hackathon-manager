import { Button } from '../../../components/ui'
import { getAttendanceParticipants } from '../api/attendanceApi'
import type { AttendanceParticipant } from '../types'
import { AttendancePagedList } from './AttendancePagedList'
import { AttendanceTeamGroup } from './AttendanceTeamGroup'

function ParticipantGroups({ participants }: { participants: AttendanceParticipant[] }) {
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
        .map(([id, group]) => <AttendanceTeamGroup key={id} {...group} />)}
    </div>
  )
}

export function AttendanceCheckInList({ hackathonPublicId }: { hackathonPublicId: string }) {
  return (
    <div className="attendance-participants">
      <Button type="button" variant="ghost" disabled
        title="Wymaga podłączenia backendu zasobów; akcja obejmie wszystkich obecnych, niezależnie od strony">
        Wyślij obecnym
      </Button>
      <p className="attendance-resource-notice">Zarządzanie zasobami nie jest jeszcze podłączone do backendu.</p>
      <p>Grupowanie dotyczy bieżącej strony uczestników. Pełne składy znajdziesz w widoku „Drużyny”.</p>
      <AttendancePagedList hackathonPublicId={hackathonPublicId} loadPage={getAttendanceParticipants}
        label="Lista uczestników" emptyMessage="Brak zaakceptowanych uczestników.">
        {(items) => <ParticipantGroups participants={items} />}
      </AttendancePagedList>
    </div>
  )
}
