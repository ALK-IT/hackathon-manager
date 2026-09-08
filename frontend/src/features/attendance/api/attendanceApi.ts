import { apiRequest } from '../../../lib/api/client'
import type { CheckIn, CheckInListItem, CheckInSession } from '../types'

export function createCheckInSession(
  hackathonPublicId: string,
  expiresInMinutes = 15,
) {
  return apiRequest<CheckInSession>(
    `/api/hackathons/${encodeURIComponent(hackathonPublicId)}/check-in-sessions`,
    {
      method: 'POST',
      body: JSON.stringify({ expires_in_minutes: expiresInMinutes }),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

export function checkInCurrentUser(hackathonPublicId: string, token: string) {
  return apiRequest<CheckIn>(
    `/api/hackathons/${encodeURIComponent(hackathonPublicId)}/check-ins/me`,
    {
      method: 'PUT',
      body: JSON.stringify({ token }),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

export function getCheckIns(hackathonPublicId: string, signal?: AbortSignal) {
  return apiRequest<CheckInListItem[]>(
    `/api/hackathons/${encodeURIComponent(hackathonPublicId)}/check-ins`,
    { signal },
  )
}
