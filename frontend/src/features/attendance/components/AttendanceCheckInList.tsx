import { useCallback, useEffect, useState } from 'react'
import { Alert, Button } from '../../../components/ui'
import { getCheckIns } from '../api/attendanceApi'
import type { CheckInListItem } from '../types'
import { getAttendanceErrorMessage } from '../utils/attendanceMessages'

interface AttendanceCheckInListProps {
  hackathonPublicId: string
}

export function AttendanceCheckInList({
  hackathonPublicId,
}: AttendanceCheckInListProps) {
  const [checkIns, setCheckIns] = useState<CheckInListItem[] | null>(null)
  const [isLoading, setIsLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const loadCheckIns = useCallback(async (signal?: AbortSignal) => {
    setIsLoading(true)
    setError(null)

    try {
      setCheckIns(await getCheckIns(hackathonPublicId, signal))
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

  return (
    <section
      className="attendance-participants"
      aria-label="Lista obecnych uczestników"
    >
      <div className="attendance-participants-actions">
        <Button
          type="button"
          variant="ghost"
          disabled={isLoading}
          onClick={() => void loadCheckIns()}
        >
          {isLoading ? 'Odświeżanie…' : 'Odśwież listę'}
        </Button>
      </div>

      <div aria-live="polite">
        {isLoading && checkIns === null && <p>Ładowanie uczestników…</p>}
        {error && <Alert variant="error">{error}</Alert>}
        {!isLoading && !error && checkIns?.length === 0 && (
          <p>Nikt jeszcze nie potwierdził obecności.</p>
        )}
        {checkIns && checkIns.length > 0 && (
          <ul className="attendance-participants-list">
            {checkIns.map((item) => (
              <li key={item.check_in.public_id}>
                <strong>{item.participant.name}</strong>
                <span>{item.participant.email}</span>
                <span>
                  Potwierdzono:{' '}
                  {new Date(item.check_in.checked_in_at).toLocaleString('pl-PL')}
                </span>
              </li>
            ))}
          </ul>
        )}
      </div>
    </section>
  )
}
