import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../auth'
import { deleteRegistration } from '../../registration/api/registrationApi'
import { getProfileHackathons } from '../api/profileApi'
import { ProfilePage } from './ProfilePage'

vi.mock('../api/profileApi', () => ({ getProfileHackathons: vi.fn() }))
vi.mock('../../registration/api/registrationApi', () => ({ deleteRegistration: vi.fn() }))
vi.mock('../../notifications', () => ({ NotificationBell: () => null }))

const auth: AuthContextValue = {
  user: {
    public_id: 'user-1',
    name: 'Jan Kowalski',
    email: 'jan@example.com',
    created_at: '2026-01-10T12:00:00Z',
    role: 'user',
  },
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.mocked(getProfileHackathons).mockReset()
    vi.mocked(deleteRegistration).mockReset()
  })

  afterEach(() => vi.restoreAllMocks())

  it('shows user data and accepted hackathons', async () => {
    vi.mocked(getProfileHackathons).mockResolvedValue({
      items: [{
        registration_public_id: 'registration-1',
        hackathon_public_id: 'hackathon-1',
        name: 'Build the Future',
        description: 'Weekend tworzenia produktów.',
        start_date: '2026-09-12T09:00:00Z',
        end_date: '2026-09-13T18:00:00Z',
        status: 'accepted',
        team: { public_id: 'team-1', name: 'Pixel Pioneers' },
        status_changed_at: '2026-08-20T10:00:00Z',
      }],
      total: 1,
      limit: 12,
      offset: 0,
    })

    render(
      <MemoryRouter>
        <AuthContext.Provider value={auth}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByRole('heading', { name: 'Jan Kowalski' })).toBeInTheDocument()
    expect(await screen.findByText('Build the Future')).toBeInTheDocument()
    expect(screen.getByText('Zespół: Pixel Pioneers')).toBeInTheDocument()
    expect(screen.getByText('Przyjęty')).toBeInTheDocument()
  })

  it('shows an empty state when the user has no accepted hackathons', async () => {
    vi.mocked(getProfileHackathons).mockResolvedValue({
      items: [],
      total: 0,
      limit: 12,
      offset: 0,
    })

    render(
      <MemoryRouter>
        <AuthContext.Provider value={auth}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Jeszcze nie ma tu żadnych wydarzeń')).toBeInTheDocument()
  })

  it('loads the next page without replacing visible hackathons', async () => {
    const firstHackathon = {
      registration_public_id: 'registration-1',
      hackathon_public_id: 'hackathon-1',
      name: 'Pierwszy hackathon',
      description: '',
      start_date: '2026-09-12T09:00:00Z',
      end_date: '2026-09-13T18:00:00Z',
      status: 'pending' as const,
      team: null,
      status_changed_at: null,
    }
    const secondHackathon = {
      ...firstHackathon,
      registration_public_id: 'registration-2',
      hackathon_public_id: 'hackathon-2',
      name: 'Drugi hackathon',
    }
    vi.mocked(getProfileHackathons)
      .mockResolvedValueOnce({
        items: [firstHackathon],
        total: 2,
        limit: 12,
        offset: 0,
      })
      .mockResolvedValueOnce({
        items: [secondHackathon],
        total: 2,
        limit: 12,
        offset: 1,
      })

    render(
      <MemoryRouter>
        <AuthContext.Provider value={auth}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Pierwszy hackathon')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Pokaż więcej' }))

    expect(await screen.findByText('Drugi hackathon')).toBeInTheDocument()
    expect(screen.getByText('Pierwszy hackathon')).toBeInTheDocument()
    await waitFor(() =>
      expect(getProfileHackathons).toHaveBeenLastCalledWith(12, 1),
    )
    expect(screen.queryByRole('button', { name: 'Pokaż więcej' })).not.toBeInTheDocument()
  })

  it('withdraws an upcoming hackathon from the profile card', async () => {
    vi.mocked(getProfileHackathons).mockResolvedValue({
      items: [{
        registration_public_id: 'registration-1',
        hackathon_public_id: 'hackathon-1',
        name: 'Przyszły hackathon',
        description: '',
        start_date: '2099-09-12T09:00:00Z',
        end_date: '2099-09-13T18:00:00Z',
        status: 'accepted',
        team: null,
        status_changed_at: null,
      }],
      total: 1,
      limit: 12,
      offset: 0,
    })
    vi.mocked(deleteRegistration).mockResolvedValue(undefined)
    vi.spyOn(window, 'confirm').mockReturnValue(true)

    render(
      <MemoryRouter>
        <AuthContext.Provider value={auth}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    fireEvent.click(await screen.findByRole('button', { name: 'Wycofaj zgłoszenie' }))

    await waitFor(() => expect(deleteRegistration).toHaveBeenCalledWith('registration-1'))
    expect(screen.queryByText('Przyszły hackathon')).not.toBeInTheDocument()
  })

  it('does not show withdrawal after the hackathon ends', async () => {
    vi.mocked(getProfileHackathons).mockResolvedValue({
      items: [{
        registration_public_id: 'registration-1',
        hackathon_public_id: 'hackathon-1',
        name: 'Zakończony hackathon',
        description: '',
        start_date: '2000-09-12T09:00:00Z',
        end_date: '2000-09-13T18:00:00Z',
        status: 'pending',
        team: null,
        status_changed_at: null,
      }],
      total: 1,
      limit: 12,
      offset: 0,
    })

    render(
      <MemoryRouter>
        <AuthContext.Provider value={auth}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Zakończony hackathon')).toBeInTheDocument()
    expect(
      screen.queryByRole('button', { name: 'Wycofaj zgłoszenie' }),
    ).not.toBeInTheDocument()
  })
})
