import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import {
  checkInCurrentUser,
  createCheckInSession,
  getAttendanceParticipants,
  getAttendanceSummary,
  getAttendanceTeams,
  getCheckIns,
} from './attendanceApi'

vi.mock('../../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('attendanceApi', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it.each([
    [getCheckIns, 'check-ins'],
    [getAttendanceParticipants, 'attendance'],
    [getAttendanceTeams, 'teams'],
  ] as const)('passes page parameters and cancellation signal (%s)', async (load, endpoint) => {
    const signal = new AbortController().signal
    const response = { items: [], total: 65, limit: 20, offset: 40 }
    vi.mocked(apiRequest).mockResolvedValue(response)
    expect(await load('hackathon/id', { limit: 20, offset: 40, signal })).toEqual(response)
    expect(apiRequest).toHaveBeenCalledWith(
      `/api/hackathons/hackathon%2Fid/${endpoint}?limit=20&offset=40`, { signal },
    )
  })

  it('gets summary for the selected hackathon with cancellation support', () => {
    const controller = new AbortController()
    getAttendanceSummary('hackathon/id', controller.signal)
    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon%2Fid/summary', {
      signal: controller.signal,
    })
  })

  it('creates a check-in session for the selected hackathon', () => {
    createCheckInSession('hackathon/id', 20)

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon%2Fid/check-in-sessions',
      {
        method: 'POST',
        body: JSON.stringify({ expires_in_minutes: 20 }),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })

  it('sends a scanned token for the current participant', () => {
    checkInCurrentUser('hackathon-id', 'qr-token')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/check-ins/me',
      {
        method: 'PUT',
        body: JSON.stringify({ token: 'qr-token' }),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })

  it('gets participants who confirmed their attendance', () => {
    getCheckIns('hackathon/id')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon%2Fid/check-ins?limit=50&offset=0',
      { signal: undefined },
    )
  })

  it('gets all accepted participants with their attendance status', () => {
    getAttendanceParticipants('hackathon/id')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon%2Fid/attendance?limit=50&offset=0',
      { signal: undefined },
    )
  })

  it('gets teams used to group checked-in participants', () => {
    getAttendanceTeams('hackathon/id')

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon%2Fid/teams?limit=50&offset=0',
      { signal: undefined },
    )
  })
})
