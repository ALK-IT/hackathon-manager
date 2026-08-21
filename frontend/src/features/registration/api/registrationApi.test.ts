import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import {
  createRegistration,
  getMyRegistration,
  getRegistrationQuestions,
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

  it('gets the current user registration for the selected hackathon', () => {
    getMyRegistration('hackathon-id')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/registrations/me',
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
})
