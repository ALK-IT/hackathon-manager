import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import { getProfileHackathons } from './profileApi'

vi.mock('../../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('profileApi', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it('requests a page of profile hackathons', () => {
    getProfileHackathons(12, 24)

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/profile/hackathons?limit=12&offset=24',
      { signal: undefined },
    )
  })
})
