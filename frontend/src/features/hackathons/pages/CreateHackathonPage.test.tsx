import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { createHackathon } from '../api/hackathonsApi'
import { CreateHackathonPage } from './CreateHackathonPage'

vi.mock('../api/hackathonsApi', () => ({ createHackathon: vi.fn() }))

describe('CreateHackathonPage', () => {
  beforeEach(() => vi.mocked(createHackathon).mockReset())

  it('validates required fields before sending the request', async () => {
    render(
      <MemoryRouter>
        <CreateHackathonPage />
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Utwórz hackathon' }))

    expect(await screen.findByText('Podaj nazwę hackathonu.')).toBeInTheDocument()
    expect(createHackathon).not.toHaveBeenCalled()
  })

  it('creates a hackathon and returns to the list', async () => {
    vi.mocked(createHackathon).mockResolvedValue(undefined)
    render(
      <MemoryRouter initialEntries={['/hackathons/create']}>
        <Routes>
          <Route path="/hackathons/create" element={<CreateHackathonPage />} />
          <Route path="/hackathons" element={<p>Lista hackathonów</p>} />
        </Routes>
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Nazwa'), { target: { value: 'Hackathon AI' } })
    fireEvent.change(screen.getByLabelText('Rozpoczęcie hackathonu'), {
      target: { value: '2026-09-10T10:00' },
    })
    fireEvent.change(screen.getByLabelText('Zakończenie hackathonu'), {
      target: { value: '2026-09-11T18:00' },
    })
    fireEvent.change(screen.getByLabelText('Otwarcie zapisów'), {
      target: { value: '2026-08-20T10:00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Utwórz hackathon' }))

    expect(await screen.findByText('Lista hackathonów')).toBeInTheDocument()
    expect(createHackathon).toHaveBeenCalledWith({
      name: 'Hackathon AI',
      description: '',
      start_date: new Date('2026-09-10T10:00').toISOString(),
      end_date: new Date('2026-09-11T18:00').toISOString(),
      registration_opens_at: new Date('2026-08-20T10:00').toISOString(),
      max_team_size: 4,
    })
  })
})
