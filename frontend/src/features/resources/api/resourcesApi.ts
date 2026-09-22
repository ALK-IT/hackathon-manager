import type {
  ManagedResource,
  MyResource,
  ResourceImportResponse,
  ResourceRevealResponse,
  ResourceTarget,
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
