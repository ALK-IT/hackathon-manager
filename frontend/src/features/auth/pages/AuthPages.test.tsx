import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { ApiError } from '../../../lib/api/client'
import { AuthContext, type AuthContextValue } from '../context/AuthContext'
import { LoginPage } from './LoginPage'
import { RegisterPage } from './RegisterPage'

function renderPage(page: 'login' | 'register', overrides: Partial<AuthContextValue> = {}) {
  const auth: AuthContextValue = {
    user: null,
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
    ...overrides,
  }

  render(
    <MemoryRouter initialEntries={[`/${page}`]}>
      <AuthContext.Provider value={auth}>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />
          <Route path="/hackathons" element={<div>Hackathony</div>} />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>,
  )

  return auth
}

describe('auth pages', () => {
  it('validates login fields before submission', () => {
    const auth = renderPage('login')

    fireEvent.click(screen.getByRole('button', { name: 'Zaloguj się' }))

    expect(screen.getByText('Podaj poprawny adres e-mail.')).toBeInTheDocument()
    expect(screen.getByText('Podaj hasło.')).toBeInTheDocument()
    expect(auth.login).not.toHaveBeenCalled()
  })

  it('maps a 401 login response to a user-friendly message', async () => {
    const login = vi.fn().mockRejectedValue(new ApiError(401))
    renderPage('login', { login })
    fireEvent.change(screen.getByLabelText('E-mail'), { target: { value: 'jan@example.com' } })
    fireEvent.change(screen.getByLabelText('Hasło'), { target: { value: 'password123' } })

    fireEvent.click(screen.getByRole('button', { name: 'Zaloguj się' }))

    expect(await screen.findByRole('alert')).toHaveTextContent('Nieprawidłowy e-mail lub hasło')
  })

  it('validates registration fields before submission', () => {
    const auth = renderPage('register')

    fireEvent.click(screen.getByRole('button', { name: 'Utwórz konto' }))

    expect(screen.getByText('Nazwa musi mieć co najmniej 3 znaki.')).toBeInTheDocument()
    expect(screen.getByText('Hasło musi mieć co najmniej 8 znaków.')).toBeInTheDocument()
    expect(auth.register).not.toHaveBeenCalled()
  })
})
