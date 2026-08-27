import { fireEvent, render, screen } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../auth'
import { getMyResources } from '../api/resourcesApi'
import type { MyResource } from '../types'
import { MyResourcesPage } from './MyResourcesPage'

vi.mock('../api/resourcesApi', () => ({
  getMyResources: vi.fn(),
  revealResourceValue: vi.fn(),
}))

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

const resource: MyResource = {
  public_id: 'resource-item-id',
  name: 'OpenAI API key',
  type: 'api_key',
  target: 'individual',
  metadata: {},
  is_revoked: false,
  hackathon: { public_id: 'hackathon-id', name: 'HackYeah' },
}

function renderPage() {
  return render(
    <MemoryRouter initialEntries={['/my-resources']}>
      <AuthContext.Provider value={auth}>
        <MyResourcesPage />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('MyResourcesPage', () => {
  beforeEach(() => vi.mocked(getMyResources).mockReset())

  it('shows assigned resources', async () => {
    vi.mocked(getMyResources).mockResolvedValue([resource])
    renderPage()

    expect(await screen.findByRole('heading', { name: 'OpenAI API key' })).toBeInTheDocument()
  })

  it('shows an empty state', async () => {
    vi.mocked(getMyResources).mockResolvedValue([])
    renderPage()

    expect(await screen.findByText('Nie masz jeszcze przypisanych zasobów.')).toBeInTheDocument()
  })

  it('shows an error and retries loading', async () => {
    vi.mocked(getMyResources)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce([resource])
    renderPage()

    expect(await screen.findByRole('alert')).toHaveTextContent('Nie udało się pobrać')
    fireEvent.click(screen.getByRole('button', { name: 'Spróbuj ponownie' }))

    expect(await screen.findByRole('heading', { name: 'OpenAI API key' })).toBeInTheDocument()
    expect(getMyResources).toHaveBeenCalledTimes(2)
  })
})
