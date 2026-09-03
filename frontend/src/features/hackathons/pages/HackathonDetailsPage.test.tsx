import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../auth'
import {
  addCoOrganizer,
  createHackathonTask,
  getHackathon,
  getHackathonTasks,
} from '../api/hackathonsApi'
import type { HackathonDetails } from '../types'
import { HackathonDetailsPage } from './HackathonDetailsPage'

vi.mock('../api/hackathonsApi', () => ({
  addCoOrganizer: vi.fn(),
  createHackathonTask: vi.fn(),
  getHackathon: vi.fn(),
  getHackathonTasks: vi.fn(),
}))

const ownerId = '1021c94e-1a20-4db0-a4a4-718202f41e1a'
const coOrganizerId = 'c68d217a-0ee7-4bc3-b25f-cad078df0da7'

const hackathon: HackathonDetails = {
  public_id: '7b8b88c5-21cd-4b70-a4ad-240b32f365db',
  name: 'Test Hackathon',
  description: 'Opis hackathonu',
  start_date: '2026-09-01T10:00:00Z',
  end_date: '2026-09-02T18:00:00Z',
  registration_opens_at: '2026-08-01T10:00:00Z',
  registration_deadline: '2026-08-30T10:00:00Z',
  registration_open: true,
  capacity: 100,
  max_team_size: 4,
  organizer: { public_id: ownerId, name: 'Admin' },
  co_organizers: [],
  access_level: 'owner',
  my_registration_status: null,
  created_at: '2026-07-01T10:00:00Z',
  updated_at: '2026-07-01T10:00:00Z',
}

const auth: AuthContextValue = {
  user: {
    public_id: ownerId,
    name: 'Admin',
    email: 'admin@example.com',
    created_at: '2026-07-01T10:00:00Z',
    role: 'admin',
  },
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={[`/hackathons/${hackathon.public_id}`]}>
      <AuthContext.Provider value={auth}>
        <Routes>
          <Route
            path="/hackathons/:hackathonPublicId"
            element={<HackathonDetailsPage />}
          />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('HackathonDetailsPage', () => {
  beforeEach(() => {
    vi.mocked(getHackathon).mockReset()
    vi.mocked(addCoOrganizer).mockReset()
    vi.mocked(createHackathonTask).mockReset()
    vi.mocked(getHackathonTasks).mockReset()
    vi.mocked(getHackathon).mockResolvedValue(hackathon)
    vi.mocked(getHackathonTasks).mockResolvedValue([])
  })

  it('shows public hackathon details', async () => {
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Test Hackathon' })).toBeInTheDocument()
    expect(screen.getByText('Opis hackathonu')).toBeInTheDocument()
    expect(screen.getByText('Organizator: Admin')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Zarejestruj się' })).toBeInTheDocument()
  })

  it('allows the owner to add a co-organizer and refreshes the displayed list', async () => {
    vi.mocked(addCoOrganizer).mockResolvedValue({
      ...hackathon,
      co_organizers: [{ public_id: coOrganizerId, name: 'Jan Kowalski' }],
    })
    renderPage()

    fireEvent.change(await screen.findByLabelText('Public ID użytkownika'), {
      target: { value: coOrganizerId },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Dodaj współorganizatora' }))

    await waitFor(() =>
      expect(addCoOrganizer).toHaveBeenCalledWith(hackathon.public_id, {
        user_public_id: coOrganizerId,
      }),
    )
    expect(await screen.findByText('Jan Kowalski')).toBeInTheDocument()
    expect(screen.getByText('Dodano współorganizatora: Jan Kowalski.')).toBeInTheDocument()
  })

  it('does not show management controls to a viewer', async () => {
    vi.mocked(getHackathon).mockResolvedValue({ ...hackathon, access_level: 'viewer' })
    renderPage()

    expect(await screen.findByRole('heading', { name: 'Współorganizatorzy' })).toBeInTheDocument()
    expect(screen.queryByLabelText('Public ID użytkownika')).not.toBeInTheDocument()
    expect(screen.queryByRole('button', { name: 'Dodaj zadanie' })).not.toBeInTheDocument()
  })

  it('allows a manager to add a task with its publication date', async () => {
    vi.mocked(createHackathonTask).mockResolvedValue({
      public_id: 'task-id',
      title: 'Publiczne API',
      description: 'Zbuduj API.',
      visible_from: '2026-09-01T12:00:00Z',
      created_at: '2026-08-01T10:00:00Z',
      updated_at: '2026-08-01T10:00:00Z',
    })
    renderPage()

    fireEvent.change(await screen.findByLabelText('Nazwa zadania'), {
      target: { value: 'Publiczne API' },
    })
    fireEvent.change(screen.getByLabelText('Opis zadania'), {
      target: { value: 'Zbuduj API.' },
    })
    fireEvent.change(screen.getByLabelText('Widoczne dla uczestników od'), {
      target: { value: '2026-09-01T14:00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Dodaj zadanie' }))

    await waitFor(() => expect(createHackathonTask).toHaveBeenCalledTimes(1))
    expect(await screen.findByText('Publiczne API')).toBeInTheDocument()
    expect(screen.getByText('Zadanie zostało dodane.')).toBeInTheDocument()
  })

  it('sets task publication to the hackathon start date', async () => {
    renderPage()

    const publicationField = await screen.findByLabelText(
      'Widoczne dla uczestników od',
    )
    fireEvent.change(publicationField, {
      target: { value: '2026-08-20T12:00' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Start hackathonu' }))

    const startDate = new Date(hackathon.start_date)
    const offset = startDate.getTimezoneOffset() * 60_000
    const expectedValue = new Date(startDate.getTime() - offset)
      .toISOString()
      .slice(0, 16)
    expect(publicationField).toHaveValue(expectedValue)
  })

  it('validates the public id before sending the request', async () => {
    renderPage()

    fireEvent.change(await screen.findByLabelText('Public ID użytkownika'), {
      target: { value: 'not-a-uuid' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Dodaj współorganizatora' }))

    expect(screen.getByText('Podaj poprawne public_id użytkownika.')).toBeInTheDocument()
    expect(addCoOrganizer).not.toHaveBeenCalled()
  })
})
