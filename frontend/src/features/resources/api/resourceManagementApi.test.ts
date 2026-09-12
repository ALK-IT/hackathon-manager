import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import {
  assignParticipantResources,
  createIndividualResourcePool,
  getHackathonResources,
  getParticipantResourceAssignments,
  revokeParticipantResource,
} from './resourceManagementApi'

vi.mock('../../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('resourceManagementApi', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it('lists hackathon resource pools', () => {
    getHackathonResources('hackathon/id')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon%2Fid/resources',
      { signal: undefined },
    )
  })

  it('atomically creates an individual resource pool with its keys', () => {
    createIndividualResourcePool('hackathon-id', 'Klucze API', [
      'first-secret',
      'second-secret',
    ])

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/resources',
      {
        method: 'POST',
        body: JSON.stringify({
          name: 'Klucze API',
          type: 'api_key',
          distribution_mode: 'manual',
          target: 'individual',
          metadata: {},
          values: ['first-secret', 'second-secret'],
        }),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })

  it('lists participant assignments for a resource', () => {
    getParticipantResourceAssignments('hackathon/id', 'resource/id')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon%2Fid/resources/resource%2Fid/participant-assignments',
      { signal: undefined },
    )
  })

  it('assigns available resource items to registrations', () => {
    assignParticipantResources('hackathon-id', 'resource-id', [
      'registration-id',
    ])

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/resources/resource-id/participant-assignments',
      {
        method: 'POST',
        body: JSON.stringify({
          registration_public_ids: ['registration-id'],
        }),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })

  it('revokes the resource assigned to a registration', () => {
    revokeParticipantResource(
      'hackathon-id',
      'resource-id',
      'registration/id',
    )

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/resources/resource-id/participant-assignments/registration%2Fid',
      { method: 'DELETE' },
    )
  })
})
