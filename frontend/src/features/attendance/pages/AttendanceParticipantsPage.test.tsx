import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { getAttendanceParticipants, getAttendanceTeams } from '../api/attendanceApi'
import { AttendanceParticipantsPage } from './AttendanceParticipantsPage'

vi.mock('../api/attendanceApi', () => ({
  getAttendanceParticipants: vi.fn(),
  getAttendanceTeams: vi.fn(),
  getAttendanceSummary: vi.fn().mockResolvedValue({ accepted: 0, teams: 0, present: 0, absent: 0 }),
}))

vi.mock('../../resources/components/ResourceManager', () => ({
  ResourceManager: () => <h2>Zarządzanie zasobami</h2>,
}))

vi.mock('../../evaluations/pages/SubmissionReviewPage', () => ({
  SubmissionReviewPanel: () => <h2>Lista rozwiązań</h2>,
}))

describe('AttendanceParticipantsPage', () => {
  it('displays attendance in a separate hackathon view', async () => {
    vi.mocked(getAttendanceParticipants).mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 })

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
    vi.mocked(getAttendanceTeams).mockResolvedValue({
      items: [{ public_id: 'team', name: 'Alpha', participants: [
        { public_id: 'one', name: 'Jan' }, { public_id: 'two', name: 'Anna' },
      ] }], total: 1, limit: 20, offset: 0,
    })
    fireEvent.click(screen.getByRole('tab', { name: 'Drużyny' }))
    await screen.findByRole('heading', { name: 'Alpha' })
    expect(screen.getByText('Jan')).toBeInTheDocument()
    expect(screen.getByText('Anna')).toBeInTheDocument()
    expect(screen.getByText('Łącznie: 1')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Następna strona' })).toBeDisabled()
    expect(getAttendanceTeams).toHaveBeenCalledWith('hackathon-id', expect.objectContaining({ limit: 20, offset: 0 }))
    expect(screen.queryByRole('heading', { name: 'Podsumowanie' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Podsumowanie' }))
    expect(await screen.findByRole('heading', { name: 'Podsumowanie' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Alpha' })).not.toBeInTheDocument()

    fireEvent.click(screen.getByRole('tab', { name: 'Zasoby' }))
    expect(screen.getByRole('heading', { name: 'Zarządzanie zasobami' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Podsumowanie' })).not.toBeInTheDocument()
    fireEvent.click(screen.getByRole('tab', { name: 'Rozwiązania' }))
    expect(screen.getByRole('heading', { name: 'Lista rozwiązań' })).toBeInTheDocument()
    expect(screen.queryByRole('heading', { name: 'Zarządzanie zasobami' })).not.toBeInTheDocument()
  })
})
