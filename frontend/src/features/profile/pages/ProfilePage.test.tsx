import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, useLocation } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../auth'
import { getProfileHackathons } from '../api/profileApi'
import { ProfilePage } from './ProfilePage'

vi.mock('../api/profileApi', () => ({
  getProfileHackathons: vi.fn(),
}))
vi.mock('../../notifications', () => ({ NotificationBell: () => null }))

const auth: AuthContextValue = {
  user: {
    public_id: 'user-1',
    name: 'Jan Kowalski',
    email: 'jan@example.com',
    created_at: '2026-01-10T12:00:00Z',
    role: 'user',
    language: 'pl',
  },
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  updateSettings: vi.fn(),
  logout: vi.fn(),
}

describe('ProfilePage', () => {
  beforeEach(() => {
    vi.mocked(getProfileHackathons).mockReset()
    vi.mocked(auth.updateSettings).mockReset()
  })

  it('shows user data and accepted hackathons', async () => {
    vi.mocked(getProfileHackathons).mockResolvedValue([
      {
        registration_public_id: 'registration-1',
        hackathon_public_id: 'hackathon-1',
        name: 'Build the Future',
        description: 'Weekend tworzenia produktów.',
        start_date: '2026-09-12T09:00:00Z',
        end_date: '2026-09-13T18:00:00Z',
        status: 'accepted',
        team: { public_id: 'team-1', name: 'Pixel Pioneers' },
        status_changed_at: '2026-08-20T10:00:00Z',
      },
    ])

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
    vi.mocked(getProfileHackathons).mockResolvedValue([])

    render(
      <MemoryRouter>
        <AuthContext.Provider value={auth}>
          <ProfilePage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(await screen.findByText('Jeszcze nie ma tu żadnych wydarzeń')).toBeInTheDocument()
  })

  it('opens settings from the profile button', async () => {
    vi.mocked(getProfileHackathons).mockResolvedValue([])
    function CurrentPath() {
      return <output>{useLocation().pathname}</output>
    }
    render(
      <MemoryRouter initialEntries={['/profile']}>
        <AuthContext.Provider value={auth}>
          <ProfilePage />
          <CurrentPath />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    fireEvent.click(screen.getByRole('button', { name: 'Ustawienia' }))
    expect(screen.getByText('/profile/settings')).toBeInTheDocument()
  })
})
