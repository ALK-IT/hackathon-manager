import { useEffect, useState } from 'react'
import { Alert, Button, Spinner } from '../../../components/ui'
import { getAttendanceSummary } from '../api/attendanceApi'
import type { AttendanceSummary } from '../types'
import { getAttendanceErrorMessage } from '../utils/attendanceMessages'

export function AttendanceSummaryPanel({ hackathonPublicId }: { hackathonPublicId: string }) {
  return <SummaryContent key={hackathonPublicId} hackathonPublicId={hackathonPublicId} />
}

function SummaryContent({ hackathonPublicId }: { hackathonPublicId: string }) {
  const [summary, setSummary] = useState<AttendanceSummary | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    async function load() {
      setLoading(true)
      setError(null)
      setSummary(null)
      try {
        const result = await getAttendanceSummary(hackathonPublicId, controller.signal)
        if (!controller.signal.aborted) setSummary(result)
      } catch (cause) {
        if (!controller.signal.aborted) {
          setError(getAttendanceErrorMessage(cause, 'Nie udało się pobrać podsumowania.'))
        }
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void load()
    return () => controller.abort()
  }, [hackathonPublicId, version])

  return (
    <section aria-label="Podsumowanie uczestnictwa">
      <h2>Podsumowanie</h2>
      {loading && <Spinner label="Ładowanie podsumowania…" />}
      {error && <Alert variant="error">{error}</Alert>}
      {summary && (
        <dl>
          <div><dt>Zaakceptowani</dt><dd>{summary.accepted}</dd></div>
          <div><dt>Obecni</dt><dd>{summary.present}</dd></div>
          <div><dt>Nieobecni (bez potwierdzenia)</dt><dd>{summary.absent}</dd></div>
          <div><dt>Drużyny z zaakceptowanymi uczestnikami</dt><dd>{summary.teams}</dd></div>
        </dl>
      )}
      <Button variant="ghost" disabled={loading} onClick={() => setVersion((value) => value + 1)}>
        {error ? 'Ponów pobranie podsumowania' : 'Odśwież podsumowanie'}
      </Button>
    </section>
  )
}
