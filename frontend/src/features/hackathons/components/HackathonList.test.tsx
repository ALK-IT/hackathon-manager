import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { AuthContext, type AuthContextValue } from '../../auth'
import { getHackathons } from '../api/hackathonsApi'
import type { Hackathon } from '../types'
import { HackathonList } from './HackathonList'

vi.mock('../api/hackathonsApi', () => ({ getHackathons: vi.fn() }))

const hackathon: Hackathon = {
  public_id: '7b8b88c5-21cd-4b70-a4ad-240b32f365db',
  name: 'Test Hackathon',
  start_date: '2026-09-01T10:00:00Z',
  end_date: '2026-09-02T18:00:00Z',
  registration_open: true,
  capacity: 100,
  max_team_size: 4,
  access_level: 'viewer',
  my_registration_status: null,
}

const page = (items: Hackathon[], total = items.length, offset = 0) => ({
  items,
  total,
  limit: 20,
  offset,
})

const anonymousAuth: AuthContextValue = {
  user: null,
  isLoading: false,
  login: vi.fn(),
  register: vi.fn(),
  logout: vi.fn(),
}

function renderHackathonList(auth: AuthContextValue = anonymousAuth) {
  return render(
    <MemoryRouter>
      <AuthContext.Provider value={auth}>
        <HackathonList />
      </AuthContext.Provider>
    </MemoryRouter>,
  )
}

describe('HackathonList', () => {
  beforeEach(() => vi.mocked(getHackathons).mockReset())

  it('waits for session restoration before loading hackathons', async () => {
    vi.mocked(getHackathons).mockResolvedValue(page([]))
    const { rerender } = renderHackathonList({ ...anonymousAuth, isLoading: true })

    expect(getHackathons).not.toHaveBeenCalled()

    rerender(
      <MemoryRouter>
        <AuthContext.Provider value={anonymousAuth}>
          <HackathonList />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    await waitFor(() => expect(getHackathons).toHaveBeenCalledTimes(1))
  })

  it('reloads hackathons when the authenticated user changes', async () => {
    vi.mocked(getHackathons).mockResolvedValue(page([]))
    const authenticatedAuth: AuthContextValue = {
      ...anonymousAuth,
      user: {
        public_id: 'user-1',
        name: 'Jan Kowalski',
        email: 'jan@example.com',
        created_at: '2026-08-26T10:00:00Z',
        role: 'user',
      },
    }
    const { rerender } = renderHackathonList(authenticatedAuth)

    await waitFor(() => expect(getHackathons).toHaveBeenCalledTimes(1))

    rerender(
      <MemoryRouter>
        <AuthContext.Provider value={anonymousAuth}>
          <HackathonList />
        </AuthContext.Provider>
      </MemoryRouter>,
    )

    await waitFor(() => expect(getHackathons).toHaveBeenCalledTimes(2))
  })

  it('shows a loading state while the request is pending', async () => {
    let resolveRequest: ((result: ReturnType<typeof page>) => void) | undefined
    vi.mocked(getHackathons).mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )

    renderHackathonList()

    expect(screen.getByRole('status')).toHaveTextContent('Ładowanie hackathonów')
    resolveRequest?.(page([]))
    expect(await screen.findByText('Brak hackathonów do wyświetlenia.')).toBeInTheDocument()
  })

  it('renders hackathons returned by the API', async () => {
    vi.mocked(getHackathons).mockResolvedValue(page([hackathon]))

    renderHackathonList()

    expect(await screen.findByRole('heading', { name: 'Test Hackathon' })).toBeInTheDocument()
  })

  it('shows an empty state', async () => {
    vi.mocked(getHackathons).mockResolvedValue(page([]))

    renderHackathonList()

    expect(await screen.findByText('Brak hackathonów do wyświetlenia.')).toBeInTheDocument()
  })

  it('reloads the list with selected filters', async () => {
    vi.mocked(getHackathons).mockResolvedValue(page([]))

    renderHackathonList()
    await screen.findByText('Brak hackathonów do wyświetlenia.')

    fireEvent.change(screen.getByLabelText('Termin'), { target: { value: 'true' } })
    fireEvent.change(screen.getByLabelText('Rejestracja'), {
      target: { value: 'false' },
    })

    await waitFor(() =>
      expect(getHackathons).toHaveBeenLastCalledWith(
        expect.objectContaining({
          upcoming: true,
          registrationOpen: false,
        }),
      ),
    )
  })

  it('loads hackathons page by page using the total count', async () => {
    const nextHackathon = { ...hackathon, public_id: 'next-id', name: 'Drugi hackathon' }
    vi.mocked(getHackathons)
      .mockResolvedValueOnce(page([hackathon], 21))
      .mockResolvedValueOnce(page([nextHackathon], 21, 20))

    renderHackathonList()

    expect(await screen.findByRole('heading', { name: 'Test Hackathon' })).toBeInTheDocument()
    fireEvent.click(screen.getByRole('button', { name: 'Następna strona' }))

    expect(await screen.findByRole('heading', { name: 'Drugi hackathon' })).toBeInTheDocument()
    expect(screen.getByText('Strona 2')).toBeInTheDocument()
    expect(getHackathons).toHaveBeenLastCalledWith(
      expect.objectContaining({ limit: 20, offset: 20 }),
    )
    expect(screen.getByRole('button', { name: 'Następna strona' })).toBeDisabled()
  })

  it('shows an error and retries the request', async () => {
    vi.mocked(getHackathons)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce(page([hackathon]))

    renderHackathonList()

    expect(await screen.findByRole('alert')).toHaveTextContent('Nie udało się pobrać')
    fireEvent.click(screen.getByRole('button', { name: 'Spróbuj ponownie' }))

    expect(await screen.findByRole('heading', { name: 'Test Hackathon' })).toBeInTheDocument()
    expect(getHackathons).toHaveBeenCalledTimes(2)
  })
})
