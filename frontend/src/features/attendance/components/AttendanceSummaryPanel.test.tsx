import { act, fireEvent, render, screen, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getAttendanceSummary } from '../api/attendanceApi'
import type { AttendanceSummary } from '../types'
import { AttendanceSummaryPanel } from './AttendanceSummaryPanel'

vi.mock('../api/attendanceApi', () => ({ getAttendanceSummary: vi.fn() }))
const summary = { accepted: 12, present: 8, absent: 4, teams: 3 }

describe('AttendanceSummaryPanel', () => {
  beforeEach(() => vi.resetAllMocks())

  it('loads global counters and refreshes only on request', async () => {
    vi.mocked(getAttendanceSummary).mockResolvedValue(summary)
    render(<AttendanceSummaryPanel hackathonPublicId="first" />)
    expect(screen.getByText('Ładowanie podsumowania…')).toBeInTheDocument()
    expect(await screen.findByText('12')).toBeInTheDocument()
    for (const [label, value] of [
      ['Zaakceptowani', '12'], ['Obecni', '8'],
      ['Nieobecni (bez potwierdzenia)', '4'], ['Drużyny z zaakceptowanymi uczestnikami', '3'],
    ]) {
      expect(within(screen.getByText(label).parentElement!).getByText(value)).toBeInTheDocument()
    }
    expect(getAttendanceSummary).toHaveBeenCalledTimes(1)
    vi.mocked(getAttendanceSummary).mockResolvedValue({ ...summary, present: 9, absent: 3 })
    fireEvent.click(screen.getByRole('button', { name: 'Odśwież podsumowanie' }))
    expect(await screen.findByText('9')).toBeInTheDocument()
    expect(getAttendanceSummary).toHaveBeenCalledTimes(2)
  })

  it('shows zero counters for an empty hackathon', async () => {
    vi.mocked(getAttendanceSummary).mockResolvedValue({ accepted: 0, present: 0, absent: 0, teams: 0 })
    render(<AttendanceSummaryPanel hackathonPublicId="empty" />)
    expect(await screen.findAllByText('0')).toHaveLength(4)
  })

  it('allows retry after an error without showing misleading zeros', async () => {
    vi.mocked(getAttendanceSummary).mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(summary)
    render(<AttendanceSummaryPanel hackathonPublicId="first" />)
    expect(await screen.findByRole('alert')).toHaveTextContent('Nie udało się pobrać podsumowania.')
    expect(screen.queryByText('0')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Ponów pobranie podsumowania' }))
    expect(await screen.findByText('12')).toBeInTheDocument()
  })

  it('ignores stale data after changing hackathon', async () => {
    let resolve!: (value: AttendanceSummary) => void
    vi.mocked(getAttendanceSummary).mockReturnValueOnce(new Promise((done) => { resolve = done }))
      .mockResolvedValueOnce({ accepted: 0, present: 0, absent: 0, teams: 0 })
    const { rerender } = render(<AttendanceSummaryPanel hackathonPublicId="first" />)
    const signal = vi.mocked(getAttendanceSummary).mock.calls[0][1]
    rerender(<AttendanceSummaryPanel hackathonPublicId="second" />)
    expect(await screen.findAllByText('0')).toHaveLength(4)
    await act(async () => resolve(summary))
    expect(signal?.aborted).toBe(true)
    expect(screen.queryByText('12')).not.toBeInTheDocument()
    expect(getAttendanceSummary).toHaveBeenLastCalledWith('second', expect.any(AbortSignal))
  })
})
