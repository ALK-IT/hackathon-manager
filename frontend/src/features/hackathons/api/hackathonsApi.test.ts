import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import {
  addCoOrganizer,
  createHackathonTask,
  getHackathon,
  getHackathons,
  getHackathonTasks,
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
    getHackathons({ upcoming: true, registrationOpen: false })

    expect(apiRequest).toHaveBeenCalledWith(
      '/api/hackathons?upcoming=true&open=false',
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
    }

    createHackathonTask('hackathon-id', payload)

    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hackathon-id/tasks', {
      method: 'POST',
      body: JSON.stringify(payload),
      headers: { 'Content-Type': 'application/json' },
    })
  })
})
