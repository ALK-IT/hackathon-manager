import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHackathon, getHackathonTasks } from '../../hackathons/api/hackathonsApi'
import type { HackathonDetails } from '../../hackathons/types'
import { getSubmissions } from '../api/evaluationsApi'
import { submission } from '../testFixtures'
import { SubmissionReviewPage } from './SubmissionReviewPage'

vi.mock('../../auth', () => ({ useAuth: () => ({ user: { role: 'user' }, isLoading: false }) }))
vi.mock('../../hackathons/api/hackathonsApi', () => ({ getHackathon: vi.fn(), getHackathonTasks: vi.fn() }))
vi.mock('../api/evaluationsApi', () => ({ getSubmissions: vi.fn(), saveEvaluation: vi.fn() }))

const hackathon: HackathonDetails = {
  public_id: 'hack', name: 'Test', description: '', start_date: '2000-01-01T00:00:00Z',
  end_date: '2000-01-02T00:00:00Z', registration_opens_at: '', registration_deadline: '',
  registration_open: false, capacity: null, max_team_size: 4,
  organizer: { public_id: 'owner', name: 'Owner' }, co_organizers: [], access_level: 'owner',
  my_registration_status: null, created_at: '', updated_at: '',
}

function view(query = '') {
  render(<MemoryRouter initialEntries={[`/hackathons/hack/solutions${query}`]}>
    <Routes><Route path="/hackathons/:hackathonPublicId/solutions" element={<SubmissionReviewPage />} /></Routes>
  </MemoryRouter>)
}

describe('SubmissionReviewPage', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(getHackathon).mockResolvedValue(hackathon)
    vi.mocked(getHackathonTasks).mockResolvedValue([])
    vi.mocked(getSubmissions).mockResolvedValue({ items: [submission], total: 21, limit: 20, offset: 0 })
  })
  it.each(['owner', 'co_organizer'] as const)('allows %s to evaluate after the end', async (access_level) => {
    vi.mocked(getHackathon).mockResolvedValue({ ...hackathon, access_level })
    view()
    expect(await screen.findByRole('button', { name: 'Zapisz ocenę' })).toBeInTheDocument()
  })
  it('allows only preview while the event is running', async () => {
    vi.mocked(getHackathon).mockResolvedValue({ ...hackathon, end_date: new Date(Date.now() + 60000).toISOString() })
    view()
    await screen.findByText('Drużyna Alfa — Zadanie API')
    expect(screen.queryByRole('button', { name: 'Zapisz ocenę' })).not.toBeInTheDocument()
    expect(screen.getByText('Ocenianie będzie dostępne po zakończeniu hackathonu.')).toBeInTheDocument()
  })
  it('does not request private lists for an unauthorized visitor', async () => {
    vi.mocked(getHackathon).mockResolvedValue({ ...hackathon, access_level: 'viewer' })
    view()
    expect(await screen.findByRole('alert')).toHaveTextContent('Nie masz uprawnień')
    expect(getSubmissions).not.toHaveBeenCalled()
    expect(getHackathonTasks).not.toHaveBeenCalled()
  })
  it('uses the team link filter and resets pagination after changing evaluation filter', async () => {
    view('?team=team-1')
    await screen.findByText('Drużyna Alfa — Zadanie API')
    expect(getSubmissions).toHaveBeenLastCalledWith('hack', expect.objectContaining({ teamPublicId: 'team-1', offset: 0 }))
    fireEvent.click(screen.getByRole('button', { name: 'Następna strona' }))
    await waitFor(() => expect(getSubmissions).toHaveBeenLastCalledWith('hack', expect.objectContaining({ offset: 20 })))
    fireEvent.change(screen.getByLabelText('Stan oceny'), { target: { value: 'false' } })
    await waitFor(() => expect(getSubmissions).toHaveBeenLastCalledWith('hack', expect.objectContaining({ offset: 0, evaluated: false, teamPublicId: 'team-1' })))
  })
})
