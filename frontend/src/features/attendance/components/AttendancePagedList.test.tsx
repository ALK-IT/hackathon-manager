import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import type { AttendancePage, AttendancePageOptions } from '../types'
import { AttendancePagedList } from './AttendancePagedList'

const makePage = (offset = 0, total = 21): AttendancePage<string> => ({
  items: Array.from({ length: Math.max(0, Math.min(20, total - offset)) }, (_, i) => `Person ${offset + i}`),
  total, limit: 20, offset,
})

function view(load: (id: string, options: AttendancePageOptions) => Promise<AttendancePage<string>>, id = 'event') {
  return (
    <AttendancePagedList hackathonPublicId={id} loadPage={load} label="Test" emptyMessage="Empty">
      {(items) => <ul>{items.map((item) => <li key={item}>{item}</li>)}</ul>}
    </AttendancePagedList>
  )
}

describe('AttendancePagedList', () => {
  it('uses total for navigation, requests only selected pages and refreshes the current page', async () => {
    const load = vi.fn(async (_id: string, options: AttendancePageOptions) => makePage(options.offset))
    render(view(load))
    await screen.findByText('Person 0')
    expect(screen.getByText('Łącznie: 21')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Poprzednia strona' })).toBeDisabled()
    expect(load).toHaveBeenCalledTimes(1)
    fireEvent.click(screen.getByRole('button', { name: 'Następna strona' }))
    await screen.findByText('Person 20')
    expect(screen.queryByText('Person 0')).not.toBeInTheDocument()
    expect(load).toHaveBeenLastCalledWith('event', expect.objectContaining({ limit: 20, offset: 20 }))
    expect(screen.getByRole('button', { name: 'Następna strona' })).toBeDisabled()
    fireEvent.click(screen.getByRole('button', { name: 'Odśwież listę' }))
    await waitFor(() => expect(load).toHaveBeenCalledTimes(3))
    await screen.findByText('Person 20')
    expect(load).toHaveBeenLastCalledWith('event', expect.objectContaining({ offset: 20 }))
    fireEvent.click(screen.getByRole('button', { name: 'Poprzednia strona' }))
    await screen.findByText('Person 0')
  })

  it('moves to a valid page when refreshing a deleted last page', async () => {
    const load = vi.fn<(id: string, options: AttendancePageOptions) => Promise<AttendancePage<string>>>()
      .mockResolvedValueOnce(makePage())
      .mockResolvedValueOnce(makePage(20))
      .mockResolvedValueOnce(makePage(20, 1))
      .mockResolvedValueOnce(makePage(0, 1))
    render(view(load))
    await screen.findByText('Person 0')
    fireEvent.click(screen.getByRole('button', { name: 'Następna strona' }))
    await screen.findByText('Person 20')
    fireEvent.click(screen.getByRole('button', { name: 'Odśwież listę' }))
    await screen.findByText('Łącznie: 1')
    expect(screen.getByText('Person 0')).toBeInTheDocument()
    expect(load).toHaveBeenLastCalledWith('event', expect.objectContaining({ offset: 0 }))
  })

  it('hides stale data on failure and allows retry', async () => {
    const load = vi.fn<(id: string, options: AttendancePageOptions) => Promise<AttendancePage<string>>>()
      .mockResolvedValueOnce(makePage())
      .mockRejectedValueOnce(new Error('offline'))
      .mockResolvedValueOnce(makePage(20))
    render(view(load))
    await screen.findByText('Person 0')
    fireEvent.click(screen.getByRole('button', { name: 'Następna strona' }))
    await screen.findByRole('alert')
    expect(screen.queryByText('Person 0')).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Odśwież listę' }))
    await screen.findByText('Person 20')
  })

  it('aborts old requests and ignores late responses after switching hackathons', async () => {
    let finish!: (page: AttendancePage<string>) => void
    const load = vi.fn<(id: string, options: AttendancePageOptions) => Promise<AttendancePage<string>>>()
      .mockImplementationOnce(() => new Promise((resolve) => { finish = resolve }))
      .mockResolvedValueOnce({ ...makePage(0, 1), items: ['New participant'] })
    const { rerender } = render(view(load))
    const signal = load.mock.calls[0][1].signal!
    rerender(view(load, 'other-event'))
    await screen.findByText('New participant')
    expect(signal.aborted).toBe(true)
    await act(async () => finish({ ...makePage(0, 1), items: ['Old participant'] }))
    expect(screen.queryByText('Old participant')).not.toBeInTheDocument()
    expect(load).toHaveBeenLastCalledWith('other-event', expect.objectContaining({ offset: 0 }))
  })
})
