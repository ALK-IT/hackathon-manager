import { apiRequest } from '../../../lib/api/client'
import type {
  RegistrationPayload,
  RegistrationQuestion,
  RegistrationResponse,
} from '../types'

export function getRegistrationQuestions(
  hackathonPublicId: string,
  signal?: AbortSignal,
) {
  return apiRequest<RegistrationQuestion[]>(
    `/api/hackathons/${hackathonPublicId}/questions`,
    { signal },
  )
}

export function getMyRegistration(
  hackathonPublicId: string,
  signal?: AbortSignal,
) {
  return apiRequest<RegistrationResponse>(
    `/api/hackathons/${hackathonPublicId}/registrations/me`,
    { signal },
  )
}

export function createRegistration(
  hackathonPublicId: string,
  payload: RegistrationPayload,
) {
  return apiRequest<RegistrationResponse>(
    `/api/hackathons/${hackathonPublicId}/registrations`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}
