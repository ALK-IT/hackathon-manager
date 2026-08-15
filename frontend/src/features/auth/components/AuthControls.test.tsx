import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../context/AuthContext'
import type { User } from '../types'
import { AuthControls } from './AuthControls'

const user: User = {
  public_id: 'user-1',
  name: 'Jan Kowalski',
  email: 'jan@example.com',
  created_at: '2026-08-10T10:00:00Z',
}

function renderControls(overrides: Partial<AuthContextValue> = {}) {
  const auth: AuthContextValue = {
    user: null,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  }

  render(
    <MemoryRouter initialEntries={['/hackathons']}>
      <AuthContext.Provider value={auth}>
        <Routes>
          <Route path="/hackathons" element={<AuthControls />} />
          <Route path="/" element={<div>Strona główna</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>,
  )

  return auth
}

describe('AuthControls', () => {
  it('shows the login link to an anonymous user', () => {
    renderControls()

    expect(screen.getByRole('link', { name: 'Zaloguj się' })).toHaveAttribute('href', '/login')
  })

  it('shows the user and logs them out', async () => {
    const auth = renderControls({ user })

    expect(screen.getByText('Zalogowano jako: jan@example.com')).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Wyloguj się' }))

    await waitFor(() => expect(auth.logout).toHaveBeenCalledOnce())
    expect(await screen.findByText('Strona główna')).toBeInTheDocument()
  })
})
