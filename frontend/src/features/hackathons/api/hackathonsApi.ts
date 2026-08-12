import { apiRequest } from '../../../lib/api/client'
import type { CreateHackathonPayload, Hackathon } from '../types'

export function getHackathons(options: { signal?: AbortSignal } = {}) {
  return apiRequest<Hackathon[]>('/api/hackathons', { signal: options.signal })
}

export function createHackathon(payload: CreateHackathonPayload) {
  return apiRequest<void>('/api/hackathons', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
  })
}
