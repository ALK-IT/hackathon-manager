import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { HackathonList } from './HackathonList'

describe('HackathonList', () => {
  it('renders hackathons returned by the API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () =>
          Promise.resolve([
            { public_id: 'f6bdbe89-8d10-4906-b0d0-92fc97d46eba', name: 'Test Hackathon' },
          ]),
      }),
    )

    render(<HackathonList />)

    expect(await screen.findByText(/Test Hackathon/)).toBeInTheDocument()
  })

  it('keeps the view stable when the API rejects an unauthenticated request', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: false,
        status: 401,
      }),
    )

    render(<HackathonList />)

    expect(screen.getByRole('heading', { name: 'Hackathony' })).toBeInTheDocument()
    expect(await screen.findByRole('list')).toBeEmptyDOMElement()
  })
})
