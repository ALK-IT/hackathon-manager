import { fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getAttendanceParticipants } from '../api/attendanceApi'
import { AttendanceCheckInList } from './AttendanceCheckInList'

vi.mock('../api/attendanceApi', () => ({
  getAttendanceParticipants: vi.fn(),
}))

describe('AttendanceCheckInList', () => {
  beforeEach(() => {
    vi.mocked(getAttendanceParticipants).mockReset()
  })

  it('displays all accepted participants and their presence status', async () => {
    vi.mocked(getAttendanceParticipants).mockResolvedValue([
      {
        participant: {
          public_id: 'present-participant-id',
          name: 'Jan Kowalski',
          email: 'jan@example.com',
          created_at: '2099-01-01T10:00:00Z',
        },
        registration_public_id: 'present-registration-id',
        team: { public_id: 'team-id', name: 'QR Alpha' },
        is_present: true,
        checked_in_at: '2099-09-08T12:00:00Z',
      },
      {
        participant: {
          public_id: 'absent-participant-id',
          name: 'Anna Nowak',
          email: 'anna@example.com',
          created_at: '2099-01-02T10:00:00Z',
        },
        registration_public_id: 'absent-registration-id',
        team: { public_id: 'team-id', name: 'QR Alpha' },
        is_present: false,
        checked_in_at: null,
      },
    ])
    render(<AttendanceCheckInList hackathonPublicId="hackathon-id" />)

    expect(
      await screen.findByRole('heading', { name: 'QR Alpha' }),
    ).toBeInTheDocument()
    expect(await screen.findByText('Jan Kowalski')).toBeInTheDocument()
    expect(screen.getByText('Anna Nowak')).toBeInTheDocument()
    expect(screen.getByText('jan@example.com')).toBeInTheDocument()
    expect(screen.getByText('Obecny')).toBeInTheDocument()
    expect(screen.getByText('Nieobecny')).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: 'Wyślij obecnym' }),
    ).toBeDisabled()
    const addResourceButtons = screen.getAllByRole('button', {
      name: 'Dodaj zasoby',
    })
    expect(addResourceButtons).toHaveLength(2)
    for (const button of addResourceButtons) expect(button).toBeDisabled()
    expect(
      screen.getAllByRole('button', { name: 'Cofnij zasoby' }),
    ).toHaveLength(2)

    const absentParticipantRow = screen.getByText('Anna Nowak').closest('li')
    expect(absentParticipantRow).not.toBeNull()
    expect(
      within(absentParticipantRow!).getByRole('button', {
        name: 'Dodaj zasoby',
      }),
    ).toBeInTheDocument()
    expect(
      within(absentParticipantRow!).getByRole('button', {
        name: 'Cofnij zasoby',
      }),
    ).toBeInTheDocument()
    expect(getAttendanceParticipants).toHaveBeenCalledWith(
      'hackathon-id',
      expect.any(AbortSignal),
    )
  })

  it('shows an empty state when there are no accepted participants', async () => {
    vi.mocked(getAttendanceParticipants).mockResolvedValue([])
    render(<AttendanceCheckInList hackathonPublicId="hackathon-id" />)

    expect(
      await screen.findByText('Brak zaakceptowanych uczestników.'),
    ).toBeInTheDocument()
  })

  it('refreshes the participant list on demand', async () => {
    vi.mocked(getAttendanceParticipants).mockResolvedValue([])
    render(<AttendanceCheckInList hackathonPublicId="hackathon-id" />)

    const refreshButton = await screen.findByRole('button', {
      name: 'Odśwież listę',
    })
    fireEvent.click(refreshButton)

    await waitFor(() =>
      expect(getAttendanceParticipants).toHaveBeenCalledTimes(2),
    )
    expect(getAttendanceParticipants).toHaveBeenLastCalledWith(
      'hackathon-id',
      undefined,
    )
  })

  it('shows participants without a team separately', async () => {
    vi.mocked(getAttendanceParticipants).mockResolvedValue([
      {
        participant: {
          public_id: 'participant-id',
          name: 'Jan Kowalski',
          email: 'jan@example.com',
          created_at: '2099-01-01T10:00:00Z',
        },
        registration_public_id: 'registration-id',
        team: null,
        is_present: false,
        checked_in_at: null,
      },
    ])

    render(<AttendanceCheckInList hackathonPublicId="hackathon-id" />)

    expect(
      await screen.findByRole('heading', { name: 'Bez drużyny' }),
    ).toBeInTheDocument()
  })
})
