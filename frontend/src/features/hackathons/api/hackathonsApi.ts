import { apiRequest } from '../../../lib/api/client'
import type {
  CreateHackathonPayload,
  Hackathon,
  HackathonFilters,
  UpdateHackathonPayload,
} from '../types'

interface GetHackathonsOptions extends HackathonFilters {
  signal?: AbortSignal
}

export function getHackathons(options: GetHackathonsOptions = {}) {
  const params = new URLSearchParams()
  if (options.upcoming !== undefined) {
    params.set('upcoming', String(options.upcoming))
  }
  if (options.registrationOpen !== undefined) {
    params.set('open', String(options.registrationOpen))
  }

  const query = params.toString()
  const path = query ? `/api/hackathons?${query}` : '/api/hackathons'
  return apiRequest<Hackathon[]>(path, { signal: options.signal })
}

export function createHackathon(payload: CreateHackathonPayload) {
  return apiRequest<Hackathon>('/api/hackathons', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  })
}

export function getHackathon(publicId: string) {
  return apiRequest<Hackathon>(`/api/hackathons/${publicId}`, {})
}

export function updateHackathon(
  publicId: string,
  payload: UpdateHackathonPayload,
) {
  return apiRequest<Hackathon>(`/api/hackathons/${publicId}`, {
    method: 'PATCH',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  })
}
