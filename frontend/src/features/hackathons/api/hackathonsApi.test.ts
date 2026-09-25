import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import {
  addCoOrganizer,
  createHackathonTask,
  deleteHackathon,
  getHackathon,
  getHackathons,
  getHackathonTasks,
  updateHackathonTask,
  searchCoOrganizerCandidates,
  updateHackathon,
} from './hackathonsApi'

vi.mock('../../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('getHackathons', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it('does not add query parameters when filters are not selected', () => {
    getHackathons()

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons', {
      signal: undefined,
    })
  })

  it('adds selected filters as query parameters', () => {
    getHackathons({ upcoming: true, registrationOpen: false, limit: 20, offset: 40 })

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons?upcoming=true&open=false&limit=20&offset=40',
      { signal: undefined },
    )
  })

  it('gets details of the selected hackathon', () => {
    const controller = new AbortController()

    getHackathon('hackathon-id', controller.signal)

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon-id', {
      signal: controller.signal,
    })
  })

  it('sends the co-organizer public id', () => {
    const payload = { user_public_id: 'user-id' }

    addCoOrganizer('hackathon-id', payload)

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/co-organizers',
      {
        method: 'POST',
        body: JSON.stringify(payload),
        headers: { 'Content-Type': 'application/json' },
      },
    )
  })

  it('updates hackathon settings', () => {
    const payload = {
      name: 'Nowa nazwa',
      description: '',
      start_date: '2026-09-10T08:00:00Z',
      end_date: '2026-09-11T08:00:00Z',
      registration_opens_at: '2026-08-20T08:00:00Z',
      registration_deadline: '2026-09-09T08:00:00Z',
      capacity: null,
      max_team_size: 4,
    }

    updateHackathon('hackathon-id', payload)

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon-id', {
      method: 'PATCH',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
  })

  it('deletes a hackathon with its confirmed name', () => {
    deleteHackathon('hackathon/id', 'Hackathon Demo')

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon%2Fid', {
      method: 'DELETE',
      body: JSON.stringify({ confirm_name: 'Hackathon Demo' }),
      headers: { 'Content-Type': 'application/json' },
    })
  })

  it('searches co-organizer candidates by name', () => {
    const controller = new AbortController()

    searchCoOrganizerCandidates('hackathon-id', 'Jan Kowalski', controller.signal)

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons/hackathon-id/co-organizer-candidates?query=Jan+Kowalski',
      { signal: controller.signal },
    )
  })

  it('gets tasks for the selected hackathon', () => {
    const controller = new AbortController()

    getHackathonTasks('hackathon-id', controller.signal)

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon-id/tasks', {
      signal: controller.signal,
    })
  })

  it('creates a task with its publication date', () => {
    const payload = {
      title: 'API',
      description: 'Zbuduj API.',
      visible_from: '2026-09-01T10:00:00.000Z',
      criteria: [{ name: 'Jakość', description: 'Czytelność kodu', max_points: 10 }],
    }

    createHackathonTask('hackathon-id', payload)

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon-id/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
  })

  it('updates the same task', () => {
    const payload = {
      title: 'API v2', description: 'Rozszerzony opis.',
      visible_from: '2026-09-01T10:00:00.000Z', criteria: [],
    }

    updateHackathonTask('hackathon-id', 'task/id', payload)

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon-id/tasks/task%2Fid', {
      method: 'PATCH', body: JSON.stringify(payload), headers: { 'Content-Type': 'application/json' },
    })
  })
})
