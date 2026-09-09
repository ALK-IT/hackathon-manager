import { useCallback, useEffect, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { getAttendanceParticipants } from '../api/attendanceApi'
import type { AttendanceParticipant } from '../types'
import { getAttendanceErrorMessage } from '../utils/attendanceMessages'
import { AttendanceTeamGroup } from './AttendanceTeamGroup'

interface AttendanceCheckInListProps {
  hackathonPublicId: string
}

export function AttendanceCheckInList({
  hackathonPublicId,
}: AttendanceCheckInListProps) {
  const [participants, setParticipants] = useState<
    AttendanceParticipant[] | null
  >(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadCheckIns = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true)
    setError(null)

    try {
      setParticipants(await getAttendanceParticipants(hackathonPublicId, signal))
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

  const participantGroups = new Map<
    string,
    { publicId: string; name: string; participants: AttendanceParticipant[] }
  >()
  for (const participant of participants ?? []) {
    const publicId = participant.team?.public_id ?? 'without-team'
    const group = participantGroups.get(publicId) ?? {
      publicId,
      name: participant.team?.name ?? 'Bez drużyny',
      participants: [],
    }
    group.participants.push(participant)
    participantGroups.set(publicId, group)
  }
  const teamGroups = [...participantGroups.values()].sort((first, second) =>
    first.name.localeCompare(second.name, 'pl'),
  )

  return (
    <section
      className="attendance-participants"
      aria-label="Lista uczestników"
    >
      <div className="attendance-participants-actions">
        <Button
          type="button"
          variant="ghost"
          disabled
          title="Wyśle zasoby wyłącznie uczestnikom z potwierdzoną obecnością; wymaga podłączenia backendu zasobów"
        >
          Wyślij obecnym
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
        {isLoading && participants === null && <p>Ładowanie uczestników…</p>}
        {error && <Alert variant="error">{error}</Alert>}
        {!isLoading && !error && participants?.length === 0 && (
          <p>Brak zaakceptowanych uczestników.</p>
        )}
        {participants && participants.length > 0 && (
          <div className="attendance-team-list">
            {teamGroups.map((team) => (
              <AttendanceTeamGroup
                key={team.publicId}
                name={team.name}
                participants={team.participants}
              />
            ))}
          </div>
        )}
      </div>
    </section>
  )
}
