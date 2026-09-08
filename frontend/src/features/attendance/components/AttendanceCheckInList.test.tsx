import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getCheckIns } from '../api/attendanceApi'
import { AttendanceCheckInList } from './AttendanceCheckInList'

vi.mock('../api/attendanceApi', () => ({ getCheckIns: vi.fn() }))

describe('AttendanceCheckInList', () => {
  beforeEach(() => vi.mocked(getCheckIns).mockReset())

  it('loads and displays checked-in participants on entry', async () => {
    vi.mocked(getCheckIns).mockResolvedValue([
      {
        check_in: {
          public_id: 'check-in-id',
          checked_in_at: '2099-09-08T12:00:00Z',
        },
        participant: {
          public_id: 'participant-id',
          name: 'Jan Kowalski',
          email: 'jan@example.com',
          created_at: '2099-01-01T10:00:00Z',
        },
        registration_public_id: 'registration-id',
      },
    ])
    render(<AttendanceCheckInList hackathonPublicId="hackathon-id" />)

    expect(await screen.findByText('Jan Kowalski')).toBeInTheDocument()
    expect(screen.getByText('jan@example.com')).toBeInTheDocument()
    expect(getCheckIns).toHaveBeenCalledWith(
      'hackathon-id',
      expect.any(AbortSignal),
    )
  })

  it('shows an empty state when nobody confirmed attendance', async () => {
    vi.mocked(getCheckIns).mockResolvedValue([])
    render(<AttendanceCheckInList hackathonPublicId="hackathon-id" />)

    expect(
      await screen.findByText('Nikt jeszcze nie potwierdził obecności.'),
    ).toBeInTheDocument()
  })

  it('refreshes the participant list on demand', async () => {
    vi.mocked(getCheckIns).mockResolvedValue([])
    render(<AttendanceCheckInList hackathonPublicId="hackathon-id" />)

    const refreshButton = await screen.findByRole('button', {
      name: 'Odśwież listę',
    })
    fireEvent.click(refreshButton)

    await waitFor(() => expect(getCheckIns).toHaveBeenCalledTimes(2))
    expect(getCheckIns).toHaveBeenLastCalledWith('hackathon-id', undefined)
  })
})
