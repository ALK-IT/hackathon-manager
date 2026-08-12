import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import { getHackathons } from './hackathonsApi'

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
})
