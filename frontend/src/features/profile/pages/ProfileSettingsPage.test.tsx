import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../auth'
import { sendPasswordResetLink } from '../api/profileApi'
import { ProfileSettingsPage } from './ProfileSettingsPage'

vi.mock('../api/profileApi', () => ({ sendPasswordResetLink: vi.fn() }))

const auth: AuthContextValue = {
  user: {
    public_id: 'user-1',
    name: 'janek',
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

function renderPage() {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={auth}>
        <ProfileSettingsPage />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('ProfileSettingsPage', () => {
  beforeEach(() => {
    vi.mocked(sendPasswordResetLink).mockReset()
    vi.mocked(auth.updateSettings).mockReset()
  })

  it('updates the username and language', async () => {
    vi.mocked(auth.updateSettings).mockResolvedValue({
      ...auth.user!,
      name: 'johnny',
      language: 'en',
    })
    renderPage()

    fireEvent.change(screen.getByLabelText('Username'), { target: { value: 'johnny' } })
    fireEvent.change(screen.getByLabelText('Język'), { target: { value: 'en' } })
    fireEvent.click(screen.getByRole('button', { name: 'Zapisz ustawienia' }))

    await waitFor(() =>
      expect(auth.updateSettings).toHaveBeenCalledWith({ name: 'johnny', language: 'en' }),
    )
  })

  it('sends a password reset link to the account email', async () => {
    vi.mocked(sendPasswordResetLink).mockResolvedValue({ message: 'sent' })
    renderPage()

    fireEvent.click(screen.getByRole('button', { name: 'Wyślij link do zmiany hasła' }))

    await waitFor(() => expect(sendPasswordResetLink).toHaveBeenCalledWith('jan@example.com'))
    expect(await screen.findByText(/Link do zmiany hasła został wysłany/)).toBeInTheDocument()
  })
})
