import { apiRequest } from '../../../lib/api/client'
import type { ProfileHackathon } from '../types'

export function getProfileHackathons(signal?: AbortSignal) {
  return apiRequest<ProfileHackathon[]>('/api/profile/hackathons', { signal })
}

export function sendPasswordResetLink(email: string) {
  return apiRequest<{ message: string }>('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
    headers: { 'Content-Type': 'application/json' },
    skipAuth: true,
  })
}
