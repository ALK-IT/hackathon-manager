import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes, useNavigate } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHackathon } from '../../features/hackathons/api/hackathonsApi'
import type { HackathonDetails } from '../../features/hackathons/types'
import { getAttendanceParticipants, getAttendanceSummary } from '../../features/attendance/api/attendanceApi'
import { AttendanceParticipantsPage } from '../../features/attendance/pages/AttendanceParticipantsPage'
import { RequireHackathonManager } from './RequireHackathonManager'

const auth = vi.hoisted(() => ({ user: { public_id: 'user', role: 'user' }, isLoading: false }))
vi.mock('../../features/auth', () => ({ useAuth: () => auth }))
vi.mock('../../features/hackathons/api/hackathonsApi', () => ({ getHackathon: vi.fn() }))
vi.mock('../../features/attendance/api/attendanceApi', () => ({
  getAttendanceParticipants: vi.fn(),
  getAttendanceSummary: vi.fn().mockResolvedValue({ accepted: 0, teams: 0, present: 0, absent: 0 }),
}))

const hackathon: HackathonDetails = {
  public_id: 'first', name: 'Test', description: '', start_date: '', end_date: '',
  registration_opens_at: '', registration_deadline: '', registration_open: false,
  capacity: null, max_team_size: 3, organizer: { public_id: 'owner', name: 'Owner' },
  co_organizers: [], access_level: 'owner', my_registration_status: null,
  created_at: '', updated_at: '',
}

function SwitchHackathon() {
  const navigate = useNavigate()
  return <button onClick={() => navigate('/hackathons/second/attendance')}>Zmień hackathon</button>
}

function view() {
  return render(<MemoryRouter initialEntries={['/hackathons/first/attendance']}>
    <SwitchHackathon />
    <Routes>
      <Route path="/hackathons/:hackathonPublicId/attendance" element={
        <RequireHackathonManager><AttendanceParticipantsPage /></RequireHackathonManager>
      } />
      <Route path="/hackathons/:hackathonPublicId" element={<p>Szczegóły hackathonu</p>} />
    </Routes>
  </MemoryRouter>)
}

describe('RequireHackathonManager', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(getAttendanceSummary).mockResolvedValue({ accepted: 0, teams: 0, present: 0, absent: 0 })
    auth.user = { public_id: 'user', role: 'user' }
    auth.isLoading = false
    vi.mocked(getAttendanceParticipants).mockResolvedValue([])
  })

  it.each(['owner', 'co_organizer'] as const)('allows %s to load attendance', async (access_level) => {
    vi.mocked(getHackathon).mockResolvedValue({ ...hackathon, access_level })
    view()
    expect(await screen.findByText('Brak zaakceptowanych uczestników.')).toBeInTheDocument()
    expect(getAttendanceParticipants).toHaveBeenCalledOnce()
  })

  it('allows admins even with viewer access_level', async () => {
    auth.user.role = 'admin'
    vi.mocked(getHackathon).mockResolvedValue({ ...hackathon, access_level: 'viewer' })
    view()
    expect(await screen.findByRole('heading', { name: 'Uczestnicy' })).toBeInTheDocument()
  })

  it('redirects viewers without rendering or requesting attendance', async () => {
    vi.mocked(getHackathon).mockResolvedValue({ ...hackathon, access_level: 'viewer' })
    view()
    expect(await screen.findByText('Szczegóły hackathonu')).toBeInTheDocument()
    expect(getAttendanceParticipants).not.toHaveBeenCalled()
    expect(screen.queryByRole('heading', { name: 'Uczestnicy' })).not.toBeInTheDocument()
    expect(getAttendanceSummary).not.toHaveBeenCalled()
  })

  it('does not render protected content before permission check completes', async () => {
    let resolve!: (value: HackathonDetails) => void
    vi.mocked(getHackathon).mockReturnValue(new Promise((done) => { resolve = done }))
    view()
    expect(getAttendanceParticipants).not.toHaveBeenCalled()
    expect(screen.queryByRole('heading', { name: 'Uczestnicy' })).not.toBeInTheDocument()
    await act(async () => resolve(hackathon))
    expect(await screen.findByRole('heading', { name: 'Uczestnicy' })).toBeInTheDocument()
  })

  it('shows a retryable network error instead of treating it as denied access', async () => {
    vi.mocked(getHackathon).mockRejectedValueOnce(new Error('offline')).mockResolvedValueOnce(hackathon)
    view()
    expect(await screen.findByRole('alert')).toHaveTextContent('Nie udało się sprawdzić uprawnień')
    expect(getAttendanceParticipants).not.toHaveBeenCalled()
    fireEvent.click(screen.getByRole('button', { name: 'Spróbuj ponownie' }))
    expect(await screen.findByRole('heading', { name: 'Uczestnicy' })).toBeInTheDocument()
  })

  it('ignores a late response after changing hackathon', async () => {
    let resolve!: (value: HackathonDetails) => void
    vi.mocked(getHackathon).mockReturnValueOnce(new Promise((done) => { resolve = done }))
      .mockResolvedValueOnce({ ...hackathon, public_id: 'second', access_level: 'viewer' })
    view()
    const signal = vi.mocked(getHackathon).mock.calls[0][1]
    fireEvent.click(screen.getByRole('button', { name: 'Zmień hackathon' }))
    await screen.findByText('Szczegóły hackathonu')
    await act(async () => resolve(hackathon))
    expect(signal?.aborted).toBe(true)
    expect(getAttendanceParticipants).not.toHaveBeenCalled()
  })

  it('checks permissions again after switching from an authorized hackathon', async () => {
    vi.mocked(getHackathon).mockResolvedValueOnce(hackathon)
      .mockResolvedValueOnce({ ...hackathon, public_id: 'second', access_level: 'viewer' })
    view()
    await screen.findByText('Brak zaakceptowanych uczestników.')
    fireEvent.click(screen.getByRole('button', { name: 'Zmień hackathon' }))
    await screen.findByText('Szczegóły hackathonu')
    await waitFor(() => expect(getAttendanceParticipants).toHaveBeenCalledTimes(1))
  })
})
