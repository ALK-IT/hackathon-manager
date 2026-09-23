import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import { getSubmissions, saveEvaluation } from './evaluationsApi'

vi.mock('../../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('evaluation API', () => {
  beforeEach(() => vi.clearAllMocks())
  it('passes pagination, all filters including false, and abort signal', async () => {
    const signal = new AbortController().signal
    await getSubmissions('hack/id', { limit: 20, offset: 40, teamPublicId: 'team', taskPublicId: 'task', evaluated: false, signal })
    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hack%2Fid/task-submissions?limit=20&offset=40&team_public_id=team&task_public_id=task&evaluated=false', { signal })
  })
  it('omits unused filters', async () => {
    await getSubmissions('hack', { limit: 20, offset: 0 })
    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hack/task-submissions?limit=20&offset=0', { signal: undefined })
  })
  it('sends a zero score and nullable feedback to the evaluation endpoint', async () => {
    await saveEvaluation('hack', 'task', 'submission', { score: 0, feedback: null })
    expect(apiRequest).toHaveBeenCalledWith('/api/hackathons/hack/tasks/task/submissions/submission/evaluation', {
      method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: '{"score":0,"feedback":null}',
    })
  })
})
