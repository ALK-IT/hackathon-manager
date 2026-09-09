import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getAttendanceParticipants } from '../api/attendanceApi'
import { AttendanceParticipantsPage } from './AttendanceParticipantsPage'

vi.mock('../api/attendanceApi', () => ({
  getAttendanceParticipants: vi.fn(),
}))

describe('AttendanceParticipantsPage', () => {
  it('displays attendance in a separate hackathon view', async () => {
    vi.mocked(getAttendanceParticipants).mockResolvedValue([])

    render(
      <MemoryRouter initialEntries={['/hackathons/hackathon-id/attendance']}>
        <Routes>
          <Route
            path="/hackathons/:hackathonPublicId/attendance"
            element={<AttendanceParticipantsPage />}
          />
        </Routes>
      </MemoryRouter>,
    )

    expect(
      screen.getByRole('heading', { name: 'Uczestnicy' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Wróć do hackathonu' })).toHaveAttribute(
      'href',
      '/hackathons/hackathon-id',
    )
    expect(
      await screen.findByText('Brak zaakceptowanych uczestników.'),
    ).toBeInTheDocument()
  })
})
