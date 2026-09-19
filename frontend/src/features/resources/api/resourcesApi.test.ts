import { beforeEach, describe, expect, it, vi } from 'vitest'
import { apiRequest } from '../../../lib/api/client'
import { getMyResources, revealResourceValue } from './resourcesApi'

vi.mock('../../../lib/api/client', () => ({ apiRequest: vi.fn() }))

describe('resourcesApi', () => {
  beforeEach(() => vi.mocked(apiRequest).mockReset())

  it('gets resources assigned to the current user', () => {
    const controller = new AbortController()

    getMyResources('hackathon/id', controller.signal)

    expect(apiRequest).toHaveBeenCalledWith('/api/my-resources?hackathon=hackathon%2Fid', {
      signal: controller.signal,
    })
  })

  it('reveals the selected resource item', async () => {
    vi.mocked(apiRequest).mockResolvedValue({ value: 'secret-key' })

    await expect(revealResourceValue('item/id', 'hackathon/id')).resolves.toBe('secret-key')
    expect(apiRequest).toHaveBeenCalledWith('/api/resource-items/item%2Fid/reveal?hackathon=hackathon%2Fid', {
      method: 'POST',
    })
  })
})
