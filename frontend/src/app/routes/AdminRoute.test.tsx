import { render, screen } from '@testing-library/react'
import { MemoryRouter, Route, Routes } from 'react-router-dom'
import { describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../features/auth'
import { AdminRoute } from './AdminRoute'

function auth(role: 'user' | 'admin'): AuthContextValue {
  return {
    user: {
      public_id: 'user-1',
      name: 'User',
      email: 'user@example.com',
      created_at: '2026-08-12T10:00:00Z',
      role,
    },
    isLoading: false,
    login: vi.fn(),
    register: vi.fn(),
    logout: vi.fn(),
  }
}

function renderRoute(role: 'user' | 'admin') {
  render(
    <MemoryRouter initialEntries={['/hackathons/create']}>
      <AuthContext.Provider value={auth(role)}>
        <Routes>
          <Route path="/hackathons" element={<p>Lista hackathonów</p>} />
          <Route
            path="/hackathons/create"
            element={
              <AdminRoute>
                <p>Formularz tworzenia</p>
              </AdminRoute>
            }
          />
        </Routes>
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('AdminRoute', () => {
  it('allows an administrator to enter', () => {
    renderRoute('admin')
    expect(screen.getByText('Formularz tworzenia')).toBeInTheDocument()
  })

  it('redirects a regular user to the hackathon list', async () => {
    renderRoute('user')
    expect(await screen.findByText('Lista hackathonów')).toBeInTheDocument()
  })
})
