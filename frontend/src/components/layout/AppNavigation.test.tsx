import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../features/auth'
import { AppNavigation } from './AppNavigation'

const auth: AuthContextValue = {
  user: {
    public_id: 'user-id',
    name: 'Jan Kowalski',
    email: 'jan@example.com',
    created_at: '2026-08-27T10:00:00Z',
    role: 'user',
  },
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}

function renderNavigation(value: AuthContextValue) {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={value}>
        <AppNavigation />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('AppNavigation', () => {
  it('shows the resources tab to an authenticated user', () => {
    renderNavigation(auth)

    expect(screen.getByRole('link', { name: 'Hackathony' })).toHaveAttribute(
      'href',
      '/hackathons',
    )
    expect(screen.getByRole('link', { name: 'Moje zasoby' })).toHaveAttribute(
      'href',
      '/my-resources',
    )
  })

  it('does not show the resources tab to an anonymous user', () => {
    renderNavigation({ ...auth, user: null })

    expect(screen.queryByRole('link', { name: 'Moje zasoby' })).not.toBeInTheDocument()
  })
})
