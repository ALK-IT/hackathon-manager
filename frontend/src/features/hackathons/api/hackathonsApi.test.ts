import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import {
  addCoOrganizer,
  getHackathon,
  getHackathons,
  searchCoOrganizerCandidates,
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

  it('gets details of the selected hackathon', () => {
    const controller = new AbortController()

    getHackathon('hackathon-id', controller.signal)

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon-id', {
      signal: controller.signal,
    })
  })

  it('sends the co-organizer public id', () => {
    const payload = { user_public_id: 'user-id' }

    addCoOrganizer('hackathon-id', payload)

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/co-organizers',
      {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })

  it('searches co-organizer candidates by name', () => {
    const controller = new AbortController()

    searchCoOrganizerCandidates('hackathon-id', 'Jan Kowalski', controller.signal)

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/co-organizer-candidates?query=Jan+Kowalski',
      { signal: controller.signal },
    )
  })
})
