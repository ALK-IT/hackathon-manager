import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../lib/api/client'
import { getManagedRegistrations, updateManagedRegistration } from './managementApi'

vi.mock('../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('managementApi', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it('gets registrations', () => {
    const controller = new AbortController()
    getManagedRegistrations('hackathon-id', {
      limit: 51,
      offset: 50,
      signal: controller.signal,
    })
    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/registrations?limit=51&offset=50',
      { signal: controller.signal },
    )
  })

  it('updates status', () => {
    updateManagedRegistration('registration-id', 'rejected')
    expect(apiRequest).toHaveBeenCalledWith('/api/registrations/registration-id/status', {
      method: 'PATCH',
      body: JSON.stringify({ status: 'rejected' }),
      headers: { 'Content-Type': 'application/json' },
    })
  })
})
