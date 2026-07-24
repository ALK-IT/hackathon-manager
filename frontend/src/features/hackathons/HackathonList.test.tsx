import { describe, expect, it, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import { HackathonList } from './HackathonList'

describe('HackathonList', () => {
  it('renders hackathons returned by the API', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        json: () => Promise.resolve([{ id: 1, name: 'Test Hackathon' }]),
      }),
    )

    render(<HackathonList />)

    expect(await screen.findByText(/Test Hackathon/)).toBeInTheDocument()
  })
})
