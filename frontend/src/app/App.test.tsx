import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../features/auth'
import { getHackathons } from '../features/hackathons/api/hackathonsApi'
import App from './App'

vi.mock('../features/hackathons/api/hackathonsApi', () => ({ getHackathons: vi.fn() }))

const anonymousAuth: AuthContextValue = {
  user: null,
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}

describe('App', () => {
  it.each(['/', '/hackathons'])(
    'shows the public hackathon list and login link at %s',
    async (path) => {
      vi.mocked(getHackathons).mockResolvedValue([])

      render(
        <MemoryRouter initialEntries={[path]}>
          <AuthContext.Provider value={anonymousAuth}>
            <App />
          </AuthContext.Provider>
        </MemoryRouter>,
      )

      expect(screen.getByRole('heading', { name: 'Hackathony' })).toBeInTheDocument()
      expect(screen.getByRole('link', { name: 'Zaloguj się' })).toHaveAttribute('href', '/login')
      expect(await screen.findByText('Brak hackathonów do wyświetlenia.')).toBeInTheDocument()
    },
  )
})
