import { useCallback, useEffect, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { getAttendanceTeams, getCheckIns } from '../api/attendanceApi'
import type { AttendanceTeam, CheckInListItem } from '../types'
import { getAttendanceErrorMessage } from '../utils/attendanceMessages'
import { AttendanceTeamGroup } from './AttendanceTeamGroup'

interface AttendanceCheckInListProps {
  hackathonPublicId: string
}

export function AttendanceCheckInList({
  hackathonPublicId,
}: AttendanceCheckInListProps) {
  const [checkIns, setCheckIns] = useState<CheckInListItem[] | null>(null)
  const [teams, setTeams] = useState<AttendanceTeam[] | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadCheckIns = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true)
    setError(null)

    try {
      const [loadedCheckIns, loadedTeams] = await Promise.all([
        getCheckIns(hackathonPublicId, signal),
        getAttendanceTeams(hackathonPublicId, signal),
      ])
      setCheckIns(loadedCheckIns)
      setTeams(loadedTeams)
    } catch (requestError) {
      if (requestError instanceof Error && requestError.name === 'AbortError') {
        return
      }
      setError(
        getAttendanceErrorMessage(
          requestError,
          'Nie udało się pobrać listy uczestników.',
        ),
      )
    } finally {
      if (!signal?.aborted) setIsLoading(false)
    }
  }, [hackathonPublicId])

  useEffect(() => {
    const controller = new AbortController()
    void loadCheckIns(controller.signal)

    return () => controller.abort()
  }, [loadCheckIns])

  const checkedInByParticipantId = new Map(
    checkIns?.map((item) => [item.participant.public_id, item]) ?? [],
  )
  const groupedParticipantIds = new Set<string>()
  const teamGroups = (teams ?? [])
    .map((team) => {
      const participants = team.participants.flatMap((participant) => {
        const checkIn = checkedInByParticipantId.get(participant.public_id)
        if (!checkIn) return []
        groupedParticipantIds.add(participant.public_id)
        return [checkIn]
      })
      return { publicId: team.public_id, name: team.name, participants }
    })
    .filter((team) => team.participants.length > 0)
  const participantsWithoutTeam = (checkIns ?? []).filter(
    (item) => !groupedParticipantIds.has(item.participant.public_id),
  )

  return (
    <section
      className="attendance-participants"
      aria-label="Lista obecnych uczestników"
    >
      <div className="attendance-participants-actions">
        <Button
          type="button"
          variant="ghost"
          disabled
          title="Wymaga podłączenia backendu zasobów"
        >
          Wyślij wszystkim
        </Button>
        <Button
          type="button"
          variant="ghost"
          disabled={isLoading}
          onClick={() => void loadCheckIns()}
        >
          {isLoading ? 'Odświeżanie…' : 'Odśwież listę'}
        </Button>
      </div>

      <p className="attendance-resource-notice">
        Zarządzanie zasobami nie jest jeszcze podłączone do backendu.
      </p>

      <div aria-live="polite">
        {isLoading && checkIns === null && <p>Ładowanie uczestników…</p>}
        {error && <Alert variant="error">{error}</Alert>}
        {!isLoading && !error && checkIns?.length === 0 && (
          <p>Nikt jeszcze nie potwierdził obecności.</p>
        )}
        {checkIns && checkIns.length > 0 && teams && (
          <div className="attendance-team-list">
            {teamGroups.map((team) => (
              <AttendanceTeamGroup
                key={team.publicId}
                name={team.name}
                participants={team.participants}
              />
            ))}
            {participantsWithoutTeam.length > 0 && (
              <AttendanceTeamGroup
                name="Bez drużyny"
                participants={participantsWithoutTeam}
              />
            )}
          </div>
        )}
      </div>
    </section>
  )
}
