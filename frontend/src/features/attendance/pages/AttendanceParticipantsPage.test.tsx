import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getCheckIns } from '../api/attendanceApi'
import { AttendanceParticipantsPage } from './AttendanceParticipantsPage'

vi.mock('../api/attendanceApi', () => ({ getCheckIns: vi.fn() }))

describe('AttendanceParticipantsPage', () => {
  it('displays attendance in a separate hackathon view', async () => {
    vi.mocked(getCheckIns).mockResolvedValue([])

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
      screen.getByRole('heading', { name: 'Obecni uczestnicy' }),
    ).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Wróć do hackathonu' })).toHaveAttribute(
      'href',
      '/hackathons/hackathon-id',
    )
    expect(
      await screen.findByText('Nikt jeszcze nie potwierdził obecności.'),
    ).toBeInTheDocument()
  })
})
