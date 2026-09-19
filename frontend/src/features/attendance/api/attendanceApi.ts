import { apiRequest } from '../../../lib/api/client'
import type {
  AttendanceParticipant,
  AttendancePage,
  AttendancePageOptions,
  AttendanceTeam,
  CheckIn,
  CheckInListItem,
  CheckInSession,
} from '../types'

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

function getPage<T>(
  hackathonPublicId: string,
  endpoint: string,
  { limit = 50, offset = 0, signal }: AttendancePageOptions,
) {
  const query = new URLSearchParams({ limit: String(limit), offset: String(offset) })
  return apiRequest<AttendancePage<T>>(
    `/api/hackathons/${encodeURIComponent(hackathonPublicId)}/${endpoint}?${query}`,
    { signal },
  )
}

export function getCheckIns(hackathonPublicId: string, options: AttendancePageOptions = {}) {
  return getPage<CheckInListItem>(hackathonPublicId, 'check-ins', options)
}

export function getAttendanceParticipants(
  hackathonPublicId: string,
  options: AttendancePageOptions = {},
) {
  return getPage<AttendanceParticipant>(hackathonPublicId, 'attendance', options)
}

export function getAttendanceTeams(
  hackathonPublicId: string,
  options: AttendancePageOptions = {},
) {
  return getPage<AttendanceTeam>(hackathonPublicId, 'teams', options)
}
