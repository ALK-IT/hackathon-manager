import { apiRequest } from '../../../lib/api/client'
import type { ProfileHackathon } from '../types'

export function getProfileHackathons(signal?: AbortSignal) {
  return apiRequest<ProfileHackathon[]>('/api/profile/hackathons', { signal })
}
