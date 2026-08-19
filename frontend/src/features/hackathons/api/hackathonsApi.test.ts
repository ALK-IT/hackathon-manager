import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import {
  createHackathon,
  getHackathon,
  getHackathons,
  updateHackathon,
} from './hackathonsApi'

vi.mock('../../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('getHackathons', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it('does not add query parameters when filters are not selected', () => {
    getHackathons()

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons', {
      signal: undefined,
    })
  })

  it('adds selected filters as query parameters', () => {
    getHackathons({ upcoming: true, registrationOpen: false })

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons?upcoming=true&open=false',
      { signal: undefined },
    )
  })

  it('creates a hackathon and returns its data', () => {
    const payload = {
      name: 'Hackathon AI',
      description: '',
      start_date: '2026-09-10T10:00:00Z',
      end_date: '2026-09-11T18:00:00Z',
      registration_opens_at: '2026-08-20T10:00:00Z',
      max_team_size: 4,
    }

    createHackathon(payload)

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons', {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
  })

  it('gets and updates a hackathon', () => {
    const payload = {
      name: 'Updated Hackathon',
      description: 'Updated description',
      start_date: '2026-09-10T10:00:00.000Z',
      end_date: '2026-09-11T18:00:00.000Z',
      registration_opens_at: '2026-08-20T10:00:00.000Z',
      registration_deadline: '2026-09-09T10:00:00.000Z',
      capacity: null,
      max_team_size: 4,
    }

    getHackathon('hackathon-id')
    updateHackathon('hackathon-id', payload)

    expect(apiRequest).toHaveBeenNthCalledWith(1, '/api/hackathons/hackathon-id', {})
    expect(apiRequest).toHaveBeenNthCalledWith(2, '/api/hackathons/hackathon-id', {
      method: 'PATCH',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
  })
})
