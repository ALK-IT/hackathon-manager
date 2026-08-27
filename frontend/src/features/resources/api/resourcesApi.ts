import { apiRequest } from '../../../lib/api/client'
import type { MyResource, ResourceRevealResponse } from '../types'

export function getMyResources(signal?: AbortSignal) {
  return apiRequest<MyResource[]>('/api/my-resources', { signal })
}

export async function revealResourceValue(resourceItemPublicId: string) {
  const response = await apiRequest<ResourceRevealResponse>(
    `/api/resource-items/${encodeURIComponent(resourceItemPublicId)}/reveal`,
    { method: 'POST' },
  )
  return response.value
}
