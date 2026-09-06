import { apiRequest } from '../../../lib/api/client'
import type {
  AddCoOrganizerPayload,
  CreateHackathonPayload,
  Hackathon,
  HackathonDetails,
  HackathonFilters,
  HackathonPage,
  UpdateHackathonPayload,
} from '../types'

interface GetHackathonsOptions extends HackathonFilters {
  signal?: AbortSignal
  limit?: number
  offset?: number
}

export function getHackathons(options: GetHackathonsOptions = {}) {
  const params = new URLSearchParams()
  if (options.upcoming !== undefined) {
    params.set('upcoming', String(options.upcoming))
  }
  if (options.registrationOpen !== undefined) {
    params.set('open', String(options.registrationOpen))
  }
  if (options.limit !== undefined) {
    params.set('limit', String(options.limit))
  }
  if (options.offset !== undefined) {
    params.set('offset', String(options.offset))
  }

  const query = params.toString()
  const path = query ? `/api/hackathons?${query}` : '/api/hackathons'
  return apiRequest<HackathonPage>(path, { signal: options.signal })
}

export function createHackathon(payload: CreateHackathonPayload) {
  return apiRequest<Hackathon>('/api/hackathons', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  })
}

export function getHackathon(publicId: string, signal?: AbortSignal) {
  return apiRequest<HackathonDetails>(`/api/hackathons/${encodeURIComponent(publicId)}`, {
    signal,
  })
}

export function addCoOrganizer(publicId: string, payload: AddCoOrganizerPayload) {
  return apiRequest<HackathonDetails>(
    `/api/hackathons/${encodeURIComponent(publicId)}/co-organizers`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

export function updateHackathon(publicId: string, payload: UpdateHackathonPayload) {
  return apiRequest<HackathonDetails>(`/api/hackathons/${encodeURIComponent(publicId)}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  })
}
