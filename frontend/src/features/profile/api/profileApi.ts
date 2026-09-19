import { apiRequest } from '../../../lib/api/client'
import type { ProfileHackathonListResponse } from '../types'

export function getProfileHackathons(
  limit = 50,
  offset = 0,
  signal?: AbortSignal,
) {
  const query = new URLSearchParams({
    limit: String(limit),
    offset: String(offset),
  })
  return apiRequest<ProfileHackathonListResponse>(
    `/api/profile/hackathons?${query}`,
    { signal },
  )
}
