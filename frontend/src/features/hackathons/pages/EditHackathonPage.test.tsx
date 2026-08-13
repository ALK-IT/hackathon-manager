import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHackathon, updateHackathon } from '../api/hackathonsApi'
import type { HackathonDetails } from '../types'
import { EditHackathonPage } from './EditHackathonPage'

vi.mock('../api/hackathonsApi', () => ({
  getHackathon: vi.fn(),
  updateHackathon: vi.fn(),
}))

const hackathon: HackathonDetails = {
  public_id: 'hackathon-id',
  name: 'Hackathon AI',
  description: 'Opis',
  start_date: '2026-09-10T08:00:00Z',
  end_date: '2026-09-11T16:00:00Z',
  registration_opens_at: '2026-08-20T08:00:00Z',
  registration_deadline: '2026-09-08T08:00:00Z',
  registration_open: true,
  capacity: 100,
  max_team_size: 4,
  access_level: 'owner',
  organizer: { public_id: 'admin-id', name: 'Admin' },
  co_organizers: [],
  created_at: '2026-08-13T10:00:00Z',
  updated_at: '2026-08-13T10:00:00Z',
}

function renderPage() {
  render(
    <MemoryRouter initialEntries={['/hackathons/hackathon-id/settings']}>
      <Routes>
        <Route
          path="/hackathons/:hackathonPublicId/settings"
          element={<EditHackathonPage />}
        />
        <Route path="/hackathons" element={<p>Lista hackathonów</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('EditHackathonPage', () => {
  beforeEach(() => {
    vi.mocked(getHackathon).mockReset()
    vi.mocked(updateHackathon).mockReset()
  })

  it('loads current settings and saves changes', async () => {
    vi.mocked(getHackathon).mockResolvedValue(hackathon)
    vi.mocked(updateHackathon).mockResolvedValue({
      ...hackathon,
      name: 'Nowa nazwa',
    })
    renderPage()

    const nameInput = await screen.findByLabelText('Nazwa')
    expect(nameInput).toHaveValue('Hackathon AI')
    fireEvent.change(nameInput, { target: { value: 'Nowa nazwa' } })
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz ustawienia' }))

    expect(await screen.findByText('Lista hackathonów')).toBeInTheDocument()
    expect(updateHackathon).toHaveBeenCalledWith(
      'hackathon-id',
      expect.objectContaining({
        name: 'Nowa nazwa',
        description: 'Opis',
        capacity: 100,
        max_team_size: 4,
      }),
    )
  })

  it('shows an error when settings cannot be loaded', async () => {
    vi.mocked(getHackathon).mockRejectedValue(new Error('Network error'))
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Nie udało się zapisać ustawień hackathonu',
    )
    expect(screen.queryByRole('button', { name: 'Zapisz ustawienia' })).not.toBeInTheDocument()
  })
})
