import { apiRequest } from '../../../lib/api/client'
import type {
  ParticipantArea,
  RegistrationPayload,
  RegistrationQuestion,
  RegistrationQuestionPayload,
  RegistrationResponse,
  TaskSubmission,
} from '../types'

export function getParticipantArea(
  hackathonPublicId: string,
  signal?: AbortSignal,
) {
  return apiRequest<ParticipantArea>(
    `/api/hackathons/${hackathonPublicId}/participant-area`,
    { signal },
  )
}

export function saveTaskSubmission(
  hackathonPublicId: string,
  taskPublicId: string,
  githubUrl: string,
) {
  return apiRequest<TaskSubmission>(
    `/api/hackathons/${hackathonPublicId}/tasks/${taskPublicId}/submission`,
    {
      method: 'PUT',
      body: JSON.stringify({ github_url: githubUrl }),
      headers: { 'Content-Type': 'application/json' },
    },
  )
}

export function getRegistrationQuestions(
  hackathonPublicId: string,
  signal?: AbortSignal,
) {
  return apiRequest<RegistrationQuestion[]>(
    `/api/hackathons/${hackathonPublicId}/questions`,
    { signal },
  )
}

export function createRegistrationQuestions(
  hackathonPublicId: string,
  questions: RegistrationQuestionPayload[],
) {
  return apiRequest<RegistrationQuestion[]>(
    `/api/hackathons/${hackathonPublicId}/questions/bulk`,
    {
      method: 'POST',
      body: JSON.stringify({ questions }),
      headers: { 'Content-Type': 'application/json' },
    },
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
