import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHackathon, updateHackathon } from '../api/hackathonsApi'
import { ApiError } from '../../../lib/api/client'
import type { HackathonDetails } from '../types'
import { EditHackathonPage } from './EditHackathonPage'

vi.mock('../api/hackathonsApi', () => ({ getHackathon: vi.fn(), updateHackathon: vi.fn() }))

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
  my_registration_status: null,
  organizer: { public_id: 'admin-id', name: 'Admin' },
  co_organizers: [],
  created_at: '2026-08-13T10:00:00Z',
  updated_at: '2026-08-13T10:00:00Z',
}

function renderPage() {
  render(
    <MemoryRouter initialEntries={['/hackathons/hackathon-id/settings']}>
      <Routes>
        <Route path="/hackathons/:hackathonPublicId/settings" element={<EditHackathonPage />} />
        <Route path="/hackathons/:hackathonPublicId" element={<p>Szczegóły</p>} />
      </Routes>
    </MemoryRouter>,
  )
}

describe('EditHackathonPage', () => {
  beforeEach(() => {
    vi.mocked(getHackathon).mockReset()
    vi.mocked(updateHackathon).mockReset()
  })

  it('loads and saves settings', async () => {
    vi.mocked(getHackathon).mockResolvedValue(hackathon)
    vi.mocked(updateHackathon).mockResolvedValue(hackathon)
    renderPage()

    const name = await screen.findByLabelText('Nazwa')
    fireEvent.change(name, { target: { value: 'Nowa nazwa' } })
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz ustawienia' }))

    expect(await screen.findByText('Szczegóły')).toBeInTheDocument()
    expect(updateHackathon).toHaveBeenCalledWith(
      'hackathon-id',
      expect.objectContaining({ name: 'Nowa nazwa', capacity: 100, max_team_size: 4 }),
    )
  })

  it('shows a loading error', async () => {
    vi.mocked(getHackathon).mockRejectedValue(new Error('network'))
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Nie udało się pobrać szczegółów hackathonu. Spróbuj ponownie.',
    )
  })

  it('validates settings before sending the update', async () => {
    vi.mocked(getHackathon).mockResolvedValue(hackathon)
    renderPage()

    fireEvent.change(await screen.findByLabelText('Zakończenie hackathonu'), {
      target: { value: '2026-09-09T10:00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz ustawienia' }))

    expect(
      await screen.findByText('Zakończenie musi być późniejsze niż rozpoczęcie.'),
    ).toBeInTheDocument()
    expect(updateHackathon).not.toHaveBeenCalled()
  })

  it('shows a specific permission error when saving', async () => {
    vi.mocked(getHackathon).mockResolvedValue(hackathon)
    vi.mocked(updateHackathon).mockRejectedValue(new ApiError(403))
    renderPage()

    await screen.findByLabelText('Nazwa')
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz ustawienia' }))

    expect(await screen.findByRole('alert')).toHaveTextContent(
      'Nie masz uprawnień do edycji tego hackathonu.',
    )
  })
})
