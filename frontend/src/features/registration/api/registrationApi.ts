import { apiRequest } from '../../../lib/api/client'
import type {
  RegistrationPayload,
  RegistrationQuestion,
  RegistrationQuestionBulkPayload,
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

export function createRegistrationQuestions(
  hackathonPublicId: string,
  payload: RegistrationQuestionBulkPayload,
) {
  return apiRequest<RegistrationQuestion[]>(
    `/api/hackathons/${hackathonPublicId}/questions/bulk`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}
