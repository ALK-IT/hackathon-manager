import { apiRequest } from '../../../lib/api/client'
import type {
  ParticipantResourceAssignment,
  ParticipantResourceAssignmentsResult,
  ResourceInventory,
  ResourceResponse,
} from '../types'

function resourcePath(hackathonPublicId: string, resourcePublicId?: string) {
  const basePath = `/api/hackathons/${encodeURIComponent(hackathonPublicId)}/resources`
  return resourcePublicId
    ? `${basePath}/${encodeURIComponent(resourcePublicId)}`
    : basePath
}

export function getHackathonResources(
  hackathonPublicId: string,
  signal?: AbortSignal,
) {
  return apiRequest<ResourceInventory[]>(resourcePath(hackathonPublicId), {
    signal,
  })
}

export function createIndividualResourcePool(
  hackathonPublicId: string,
  name: string,
  values: string[],
) {
  return apiRequest<ResourceResponse>(resourcePath(hackathonPublicId), {
    method: 'POST',
    body: JSON.stringify({
      name,
      type: 'api_key',
      distribution_mode: 'manual',
      target: 'individual',
      metadata: {},
      values,
    }),
    headers: { 'Content-Type': 'application/json' },
  })
}

export function getParticipantResourceAssignments(
  hackathonPublicId: string,
  resourcePublicId: string,
  signal?: AbortSignal,
) {
  return apiRequest<ParticipantResourceAssignment[]>(
    `${resourcePath(hackathonPublicId, resourcePublicId)}/participant-assignments`,
    { signal },
  )
}

export function assignParticipantResources(
  hackathonPublicId: string,
  resourcePublicId: string,
  registrationPublicIds: string[],
) {
  return apiRequest<ParticipantResourceAssignmentsResult>(
    `${resourcePath(hackathonPublicId, resourcePublicId)}/participant-assignments`,
    {
      method: 'POST',
      body: JSON.stringify({
        registration_public_ids: registrationPublicIds,
      }),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

export function revokeParticipantResource(
  hackathonPublicId: string,
  resourcePublicId: string,
  registrationPublicId: string,
) {
  return apiRequest<void>(
    `${resourcePath(hackathonPublicId, resourcePublicId)}/participant-assignments/${encodeURIComponent(registrationPublicId)}`,
    { method: 'DELETE' },
  )
}
