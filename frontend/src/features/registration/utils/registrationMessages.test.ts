import { describe, expect, it } from 'vitest'
import { ApiError } from '../../../lib/api/client'
import { getRegistrationErrorMessage } from './registrationMessages'

describe('getRegistrationErrorMessage', () => {
  it.each([
    ['ALREADY_REGISTERED', 'Masz już zgłoszenie do tego hackathonu.'],
    ['TEAM_NAME_TAKEN', 'Drużyna o tej nazwie już istnieje w tym hackathonie.'],
  ])('maps %s without parsing backend detail', (errorCode, expectedMessage) => {
    const error = new ApiError(409, {
      error_code: errorCode,
      detail: 'Backend message may change.',
    })

    expect(getRegistrationErrorMessage(error)).toBe(expectedMessage)
  })
})
