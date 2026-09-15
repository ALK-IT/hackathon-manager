import { useEffect, useState, type ReactNode } from 'react'
import { Alert, Button } from '../../../components/ui'
import type { AttendancePage, AttendancePageOptions } from '../types'
import { getAttendanceErrorMessage } from '../utils/attendanceMessages'

const PAGE_SIZE = 20

interface Props<T> {
  hackathonPublicId: string
  loadPage: (id: string, options: AttendancePageOptions) => Promise<AttendancePage<T>>
  label: string
  emptyMessage: string
  children: (items: T[]) => ReactNode
}

export function AttendancePagedList<T>(props: Props<T>) {
  return <PagedList key={props.hackathonPublicId} {...props} />
}

function PagedList<T>({ hackathonPublicId, loadPage, label, emptyMessage, children }: Props<T>) {
  const [page, setPage] = useState(0)
  const [result, setResult] = useState<AttendancePage<T> | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [version, setVersion] = useState(0)

  useEffect(() => {
    const controller = new AbortController()
    setLoading(true)
    setError(null)
    setResult(null)

    async function load() {
      try {
        const next = await loadPage(hackathonPublicId, {
          limit: PAGE_SIZE, offset: page * PAGE_SIZE, signal: controller.signal,
        })
        if (controller.signal.aborted) return
        // Refreshing can remove the last page when participants leave the list.
        const lastPage = Math.max(0, Math.ceil(next.total / PAGE_SIZE) - 1)
        if (page > lastPage) {
          setPage(lastPage)
          return
        }
        setResult(next)
      } catch (requestError) {
        if (controller.signal.aborted) return
        setError(getAttendanceErrorMessage(requestError, 'Nie udało się pobrać listy.'))
      } finally {
        if (!controller.signal.aborted) setLoading(false)
      }
    }
    void load()
    return () => controller.abort()
  }, [hackathonPublicId, loadPage, page, version])

  return (
    <section aria-label={label} aria-busy={loading}>
      <Button type="button" variant="ghost" disabled={loading}
        onClick={() => setVersion((current) => current + 1)}>
        {loading ? 'Odświeżanie…' : 'Odśwież listę'}
      </Button>
      <div aria-live="polite">
        {loading && <p>Ładowanie listy…</p>}
        {error && <Alert variant="error">{error}</Alert>}
        {!loading && !error && result && (
          <>
            <p>Łącznie: {result.total}</p>
            {result.total === 0 ? <p>{emptyMessage}</p> : children(result.items)}
          </>
        )}
      </div>
      {!loading && !error && result && result.total > 0 && (
        <nav aria-label={`Stronicowanie: ${label}`}>
          <Button type="button" variant="ghost" disabled={page === 0}
            onClick={() => setPage((current) => current - 1)}>Poprzednia strona</Button>
          <span aria-live="polite"> Strona {page + 1} z {Math.ceil(result.total / PAGE_SIZE)} </span>
          <Button type="button" variant="ghost"
            disabled={result.offset + result.items.length >= result.total}
            onClick={() => setPage((current) => current + 1)}>Następna strona</Button>
        </nav>
      )}
    </section>
  )
}
