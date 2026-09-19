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

export function sendPasswordResetLink(email: string) {
  return apiRequest<{ message: string }>('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
    headers: { 'Content-Type': 'application/json' },
    skipAuth: true,
  })
}
