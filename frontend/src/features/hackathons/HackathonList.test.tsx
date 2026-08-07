import { cleanup, render, screen } from '@testing-library/react'
import { afterEach, describe, expect, it, vi } from 'vitest'
import { HackathonList } from './HackathonList'

describe('HackathonList', () => {
  afterEach(() => {
    cleanup()
    vi.unstubAllGlobals()
  })

  it('shows a loading state while the request is pending', () => {
    vi.stubGlobal('fetch', vi.fn(() => new Promise(() => {})))

    render(<HackathonList />)

    expect(screen.getByRole('status')).toHaveTextContent('Loading hackathons…')
  })

  it('renders hackathons returned by the API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([{ id: 1, name: 'Test Hackathon' }]),
      }),
    )

    render(<HackathonList />)

    expect(await screen.findByText(/Test Hackathon/)).toBeInTheDocument()
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
  })

  it('shows an error when the request fails', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('Network error')))

    render(<HackathonList />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to load hackathons')
  })

  it('shows an error when the API returns an unsuccessful response', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: vi.fn(),
      }),
    )

    render(<HackathonList />)

    expect(await screen.findByRole('alert')).toHaveTextContent('Failed to load hackathons')
  })
})
