import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import {
  createRegistration,
  createRegistrationQuestions,
  getMyRegistration,
  getParticipantArea,
  getRegistrationQuestions,
  saveTaskSubmission,
} from './registrationApi'

vi.mock('../../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('registrationApi', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it('gets questions for the selected hackathon', () => {
    getRegistrationQuestions('hackathon-id')

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon-id/questions', {
      signal: undefined,
    })
  })

  it('creates questions in one request', () => {
    const questions = [{ content: 'Dlaczego?', is_required: true }]

    createRegistrationQuestions('hackathon-id', questions)

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/questions/bulk',
      {
        method: 'POST',
        body: JSON.stringify({ questions }),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })

  it('gets the current user registration for the selected hackathon', () => {
    getMyRegistration('hackathon-id')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/registrations/me',
      { signal: undefined },
    )
  })

  it('gets the participant area for the selected hackathon', () => {
    getParticipantArea('hackathon-id')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/participant-area',
      { signal: undefined },
    )
  })

  it('sends the registration payload', () => {
    const payload = {
      answers: [{ question_public_id: 'question-id', content: 'Odpowiedź' }],
      team: { action: 'join' as const, join_code: 'ABCD1234' },
    }

    createRegistration('hackathon-id', payload)

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/registrations',
      {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })

  it('upserts the team solution for a task', () => {
    saveTaskSubmission('hackathon-id', 'task-id', 'https://github.com/example/repo')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/tasks/task-id/submission',
      {
        method: 'PUT',
        body: JSON.stringify({ github_url: 'https://github.com/example/repo' }),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })
})
