import { fireEvent, render, screen } from '@testing-library/react'
import { beforeEach, describe, expect, it, vi } from 'vitest'
import { getHackathons } from '../api/hackathonsApi'
import type { Hackathon } from '../types'
import { HackathonList } from './HackathonList'

vi.mock('../api/hackathonsApi', () => ({ getHackathons: vi.fn() }))

const hackathon: Hackathon = {
  id: 1,
  name: 'Test Hackathon',
}

describe('HackathonList', () => {
  beforeEach(() => vi.mocked(getHackathons).mockReset())

  it('shows a loading state while the request is pending', async () => {
    let resolveRequest: ((hackathons: Hackathon[]) => void) | undefined
    vi.mocked(getHackathons).mockReturnValue(
      new Promise((resolve) => {
        resolveRequest = resolve
      }),
    )

    render(<HackathonList />)

    expect(screen.getByRole('status')).toHaveTextContent('Ładowanie hackathonów')
    resolveRequest?.([])
    expect(await screen.findByText('Brak hackathonów do wyświetlenia.')).toBeInTheDocument()
  })

  it('renders hackathons returned by the API', async () => {
    vi.mocked(getHackathons).mockResolvedValue([hackathon])

    render(<HackathonList />)

    expect(await screen.findByText('#1 — Test Hackathon')).toBeInTheDocument()
  })

  it('shows an empty state', async () => {
    vi.mocked(getHackathons).mockResolvedValue([])

    render(<HackathonList />)

    expect(await screen.findByText('Brak hackathonów do wyświetlenia.')).toBeInTheDocument()
  })

  it('shows an error and retries the request', async () => {
    vi.mocked(getHackathons)
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce([hackathon])

    render(<HackathonList />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Nie udało się pobrać')
    fireEvent.click(screen.getByRole('button', { name: 'Spróbuj ponownie' }))

    expect(await screen.findByText('#1 — Test Hackathon')).toBeInTheDocument()
    expect(getHackathons).toHaveBeenCalledTimes(2)
  })
})
