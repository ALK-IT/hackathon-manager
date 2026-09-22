import type {
  ManagedResource,
  MyResource,
  ResourceImportResponse,
  ResourceRevealResponse,
  ResourceTarget,
  ManagedResourceItem,
  ManagedResourceAssignment,
} from '../types'
import { apiRequest } from '../../../lib/api/client'

export function createResource(
  hackathonPublicId: string,
  data: { name: string; target: ResourceTarget; metadata?: Record<string, unknown> },
) {
  return apiRequest<ManagedResource>(
    `/api/hackathons/${encodeURIComponent(hackathonPublicId)}/resources`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ type: 'api_key', distribution_mode: 'manual', ...data }),
    },
  )
}

export function importResourceItems(
  hackathonPublicId: string,
  resourcePublicId: string,
  values: string[],
) {
  return apiRequest<ResourceImportResponse>(
    `/api/hackathons/${encodeURIComponent(hackathonPublicId)}/resources/${encodeURIComponent(resourcePublicId)}/items`,
    {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ values }),
    },
  )
}

export function getManagedResources(hackathonId: string) {
  return apiRequest<ManagedResource[]>(`/api/hackathons/${encodeURIComponent(hackathonId)}/resources`)
}

export function getResourceItems(hackathonId: string, resourceId: string) {
  return apiRequest<ManagedResourceItem[]>(`/api/hackathons/${encodeURIComponent(hackathonId)}/resources/${encodeURIComponent(resourceId)}/items?limit=100`)
}

export function getResourceAssignments(hackathonId: string) {
  return apiRequest<ManagedResourceAssignment[]>(`/api/hackathons/${encodeURIComponent(hackathonId)}/resource-assignments`)
}

export function assignResource(hackathonId: string, resourceId: string, itemId: string, registrationId: string) {
  return apiRequest(`/api/hackathons/${encodeURIComponent(hackathonId)}/resources/${encodeURIComponent(resourceId)}/assignments`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ resource_item_public_id: itemId, registration_public_id: registrationId }) })
}

export function revokeResourceAssignment(hackathonId: string, assignmentId: string) {
  return apiRequest(`/api/hackathons/${encodeURIComponent(hackathonId)}/resource-assignments/${encodeURIComponent(assignmentId)}/revoke`, { method: 'POST' })
}

export function deleteManagedResource(hackathonId: string, resourceId: string) {
  return apiRequest<void>(`/api/hackathons/${encodeURIComponent(hackathonId)}/resources/${encodeURIComponent(resourceId)}`, { method: 'DELETE' })
}

export function getMyResources(hackathonPublicId: string, signal?: AbortSignal) {
  return apiRequest<MyResource[]>(
    `/api/my-resources?hackathon=${encodeURIComponent(hackathonPublicId)}`,
    { signal },
  )
}

export async function revealResourceValue(
  resourceItemPublicId: string,
  hackathonPublicId: string,
) {
  const response = await apiRequest<ResourceRevealResponse>(
    `/api/resource-items/${encodeURIComponent(resourceItemPublicId)}/reveal?hackathon=${encodeURIComponent(hackathonPublicId)}`,
    { method: 'POST' },
  )
  return response.value
}
