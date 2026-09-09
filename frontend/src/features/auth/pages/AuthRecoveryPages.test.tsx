import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import {
  forgotPasswordRequest,
  resendVerificationRequest,
  resetPasswordRequest,
  verifyEmailRequest,
} from '../api/authApi'
import { ForgotPasswordPage } from './ForgotPasswordPage'
import { ResetPasswordPage } from './ResetPasswordPage'
import { VerifyEmailPage } from './VerifyEmailPage'

vi.mock('../api/authApi', () => ({
  forgotPasswordRequest: vi.fn(),
  resendVerificationRequest: vi.fn(),
  resetPasswordRequest: vi.fn(),
  verifyEmailRequest: vi.fn(),
}))

describe('auth recovery pages', () => {
  beforeEach(() => vi.clearAllMocks())

  it('confirms the email token from the link', async () => {
    vi.mocked(verifyEmailRequest).mockResolvedValue({ message: 'ok' })

    render(
      <MemoryRouter initialEntries={['/verify-email?token=verification-token']}>
        <VerifyEmailPage />
      </MemoryRouter>,
    )

    expect(await screen.findByText(/Konto zostało potwierdzone/)).toBeInTheDocument()
    expect(verifyEmailRequest).toHaveBeenCalledWith('verification-token')
  })

  it('requests a password reset without disclosing account existence', async () => {
    vi.mocked(forgotPasswordRequest).mockResolvedValue({ message: 'ok' })
    render(
      <MemoryRouter>
        <ForgotPasswordPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'jan@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Wyślij link' }))

    expect(await screen.findByText(/Jeśli konto istnieje/)).toBeInTheDocument()
    expect(forgotPasswordRequest).toHaveBeenCalledWith('jan@example.com')
  })

  it('requests a new verification link', async () => {
    vi.mocked(resendVerificationRequest).mockResolvedValue({ message: 'ok' })
    render(
      <MemoryRouter initialEntries={['/verify-email']}>
        <VerifyEmailPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('E-mail'), {
      target: { value: 'jan@example.com' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Wyślij nowy link' }))

    expect(await screen.findByText(/wysłaliśmy nowy link/)).toBeInTheDocument()
    expect(resendVerificationRequest).toHaveBeenCalledWith('jan@example.com')
  })

  it('sets a new password using the reset token', async () => {
    vi.mocked(resetPasswordRequest).mockResolvedValue({ message: 'ok' })
    render(
      <MemoryRouter initialEntries={['/reset-password?token=reset-token']}>
        <ResetPasswordPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Nowe hasło'), {
      target: { value: 'new-password123' },
    })
    fireEvent.change(screen.getByLabelText('Powtórz nowe hasło'), {
      target: { value: 'new-password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Zmień hasło' }))

    expect(await screen.findByText(/Hasło zostało zmienione/)).toBeInTheDocument()
    expect(resetPasswordRequest).toHaveBeenCalledWith(
      'reset-token',
      'new-password123',
      'new-password123',
    )
  })

  it('offers a new reset link when the token is rejected', async () => {
    vi.mocked(resetPasswordRequest).mockRejectedValue(new Error('expired token'))
    render(
      <MemoryRouter initialEntries={['/reset-password?token=expired-token']}>
        <ResetPasswordPage />
      </MemoryRouter>,
    )

    fireEvent.change(screen.getByLabelText('Nowe hasło'), {
      target: { value: 'new-password123' },
    })
    fireEvent.change(screen.getByLabelText('Powtórz nowe hasło'), {
      target: { value: 'new-password123' },
    })
    fireEvent.click(screen.getByRole('button', { name: 'Zmień hasło' }))

    expect(await screen.findByRole('link', { name: 'Poproś o nowy link' })).toHaveAttribute(
      'href',
      '/forgot-password',
    )
  })
})
