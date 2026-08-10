import { render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../features/auth'
import App from './App'

const anonymousAuth: AuthContextValue = {
  user: null,
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}

describe('App', () => {
  it('redirects an anonymous user to login', async () => {
    render(
      <MemoryRouter initialEntries={['/hackathons']}>
        <AuthContext.Provider value={anonymousAuth}>
          <App />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    expect(await screen.findByRole('heading', { name: 'Logowanie' })).toBeInTheDocument()
  })
})
