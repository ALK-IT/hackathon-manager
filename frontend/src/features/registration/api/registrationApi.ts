import { apiRequest } from '../../../lib/api/client'
import type {
  RegistrationPayload,
  RegistrationQuestion,
  RegistrationQuestionPayload,
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

export function createRegistrationQuestion(
  hackathonPublicId: string,
  payload: RegistrationQuestionPayload,
) {
  return apiRequest<RegistrationQuestion>(
    `/api/hackathons/${hackathonPublicId}/questions`,
    {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

export function deleteRegistrationQuestion(
  hackathonPublicId: string,
  questionPublicId: string,
) {
  return apiRequest<void>(
    `/api/hackathons/${hackathonPublicId}/questions/${questionPublicId}`,
    { method: 'DELETE' },
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
