import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  getCurrentUserRequest,
  loginRequest,
  logoutRequest,
  registerRequest,
  updateUserSettingsRequest,
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
  updateUserSettingsRequest: vi.fn(),
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
  language: 'pl',
}

function Consumer() {
  const auth = useAuth()
  return (
    <div>
      <span>{auth.isLoading ? 'loading' : (auth.user?.email ?? 'anonymous')}</span>
      <button type="button" onClick={() => void auth.login('jan@example.com', 'password123')}>
        login
      </button>
      <button
        type="button"
        onClick={() => void auth.updateSettings({ name: 'John Smith', language: 'en' })}
      >
        update
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
    vi.mocked(updateUserSettingsRequest).mockReset()
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

  it('updates the current user and document language', async () => {
    const updatedUser = { ...user, name: 'John Smith', language: 'en' as const }
    vi.mocked(refreshAccessToken).mockResolvedValue(true)
    vi.mocked(getCurrentUserRequest).mockResolvedValue(user)
    vi.mocked(updateUserSettingsRequest).mockResolvedValue(updatedUser)

    render(
      <AuthProvider>
        <Consumer />
      </AuthProvider>,
    )
    await screen.findByText('jan@example.com')
    fireEvent.click(screen.getByRole('button', { name: 'update' }))

    await waitFor(() => {
      expect(updateUserSettingsRequest).toHaveBeenCalledWith({
        name: 'John Smith',
        language: 'en',
      })
      expect(document.documentElement.lang).toBe('en')
    })
  })
})
