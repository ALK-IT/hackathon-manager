import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../auth'
import { HackathonsPage } from './HackathonsPage'

vi.mock('../components/HackathonList', () => ({
  HackathonList: () => null,
}))

const auth: AuthContextValue = {
  user: {
    public_id: 'user-1',
    name: 'Admin',
    email: 'admin@example.com',
    created_at: '2026-08-12T10:00:00Z',
    role: 'admin',
  },
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}

describe('HackathonsPage', () => {
  it('displays the current admin role and create button', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider value={auth}>
          <HackathonsPage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.getByText('Rola: admin')).toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Utwórz hackathon' })).toBeInTheDocument()
  })

  it('does not display the create button to a regular user', () => {
    render(
      <MemoryRouter>
        <AuthContext.Provider
          value={{ ...auth, user: auth.user && { ...auth.user, role: 'user' } }}
        >
          <HackathonsPage />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(screen.queryByRole('button', { name: 'Utwórz hackathon' })).not.toBeInTheDocument()
  })
})
