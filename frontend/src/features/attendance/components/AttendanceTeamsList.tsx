import { getAttendanceTeams } from '../api/attendanceApi'
import { AttendancePagedList } from './AttendancePagedList'

export function AttendanceTeamsList({ hackathonPublicId }: { hackathonPublicId: string }) {
  return (
    <AttendancePagedList hackathonPublicId={hackathonPublicId} loadPage={getAttendanceTeams}
      label="Lista drużyn" emptyMessage="Brak drużyn.">
      {(teams) => (
        <div className="attendance-team-list">
          {teams.map((team) => (
            <section className="attendance-team-group" key={team.public_id} aria-label={`Drużyna ${team.name}`}>
              <h2>{team.name}</h2>
              {team.participants.length === 0 ? <p>Brak zaakceptowanych członków.</p> : (
                <ul>{team.participants.map((member) => <li key={member.public_id}>{member.name}</li>)}</ul>
              )}
            </section>
          ))}
        </div>
      )}
    </AttendancePagedList>
  )
}
