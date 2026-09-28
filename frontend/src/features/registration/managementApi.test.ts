import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest, downloadApiFile } from '../../lib/api/client'
import { exportManagedRegistrations, getManagedRegistrations, updateManagedRegistration } from './managementApi'

vi.mock('../../lib/api/client', () => ({ apiRequest: vi.fn(), downloadApiFile: vi.fn() }))

describe('managementApi', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it('exports registrations', () => {
    exportManagedRegistrations('hackathon/id')
    expect(downloadApiFile).toHaveBeenCalledWith(
      '/api/hackathons/hackathon%2Fid/registrations/export', 'registrations.csv',
    )
  })

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
