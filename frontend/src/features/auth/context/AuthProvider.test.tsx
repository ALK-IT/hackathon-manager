import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getCurrentUserRequest,
  loginRequest,
  logoutRequest,
  registerRequest,
} from '../api/authApi'
import {
  clearAccessToken,
  refreshAccessToken,
  setAccessToken,
} from '../../../lib/api/client'
import { useAuth } from '../hooks/useAuth'
import type { User } from '../types'
import { AuthProvider } from './AuthProvider'

vi.mock('../api/authApi', () => ({
  getCurrentUserRequest: vi.fn(),
  loginRequest: vi.fn(),
  logoutRequest: vi.fn(),
  registerRequest: vi.fn(),
}))

vi.mock('../../../lib/api/client', () => ({
  clearAccessToken: vi.fn(),
  refreshAccessToken: vi.fn(),
  setAccessToken: vi.fn(),
}))

const user: User = {
  public_id: 'user-1',
  name: 'Jan Kowalski',
  email: 'jan@example.com',
  created_at: '2026-08-10T10:00:00Z',
  role: 'user',
}

function Consumer() {
  const auth = useAuth()
  return (
    <div>
      <span>{auth.isLoading ? 'loading' : (auth.user?.email ?? 'anonymous')}</span>
      <button type="button" onClick={() => void auth.login('jan@example.com', 'password123')}>
        login
      </button>
    </div>
  )
}

describe('AuthProvider', () => {
  beforeEach(() => {
    vi.mocked(getCurrentUserRequest).mockReset()
    vi.mocked(loginRequest).mockReset()
    vi.mocked(logoutRequest).mockReset()
    vi.mocked(registerRequest).mockReset()
    vi.mocked(clearAccessToken).mockReset()
    vi.mocked(refreshAccessToken).mockReset()
    vi.mocked(setAccessToken).mockReset()
  })

  it('restores the user from the refresh cookie', async () => {
    vi.mocked(refreshAccessToken).mockResolvedValue(true)
    vi.mocked(getCurrentUserRequest).mockResolvedValue(user)

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    )

    expect(await screen.findByText('jan@example.com')).toBeInTheDocument()
  })

  it('keeps the access token in the API client after login', async () => {
    vi.mocked(refreshAccessToken).mockResolvedValue(false)
    vi.mocked(loginRequest).mockResolvedValue({
      access_token: 'access-token',
      token_type: 'bearer',
      expires_in: 1800,
    })
    vi.mocked(getCurrentUserRequest).mockResolvedValue(user)

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    )
    await screen.findByText('anonymous')
    fireEvent.click(screen.getByRole('button', { name: 'login' }))

    expect(await screen.findByText('jan@example.com')).toBeInTheDocument()
    expect(setAccessToken).toHaveBeenCalledWith('access-token')
  })
})
