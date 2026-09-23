import { apiRequest } from '../../../lib/api/client'
import type { MyResource, ResourceRevealResponse } from '../types'

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
