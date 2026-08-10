import { apiRequest } from '../../../lib/api/client'
import type { Hackathon } from '../types'

export function getHackathons(options: { signal?: AbortSignal } = {}) {
  return apiRequest<Hackathon[]>('/api/hackathons', { signal: options.signal })
}
