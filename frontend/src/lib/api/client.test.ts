import { afterEach, describe, expect, it, vi } from 'vitest'
import {
  apiRequest,
  ApiError,
  clearAccessToken,
  setAccessToken,
} from './client'

function jsonResponse(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), {
    status,
    headers: { 'Content-Type': 'application/json' },
  })
}

describe('apiRequest', () => {
  afterEach(() => {
    clearAccessToken()
    vi.unstubAllGlobals()
  })

  it('adds access token to requests', async () => {
    setAccessToken('access-token')
    const fetchMock = vi.fn().mockResolvedValue(jsonResponse({ ok: true }))
    vi.stubGlobal('fetch', fetchMock)

    await apiRequest('/api/example')

    const headers = new Headers(fetchMock.mock.calls[0][1]?.headers)
    expect(headers.get('Authorization')).toBe('Bearer access-token')
  })

  it('refreshes the access token after 401 and retries once', async () => {
    setAccessToken('expired-token')
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(jsonResponse({ detail: 'Unauthorized' }, 401))
      .mockResolvedValueOnce(
        jsonResponse({
          access_token: 'new-token',
          token_type: 'bearer',
          expires_in: 1800,
        }),
      )
      .mockResolvedValueOnce(jsonResponse({ value: 'success' }))
    vi.stubGlobal('fetch', fetchMock)

    const result = await apiRequest<{ value: string }>('/api/protected')

    expect(result).toEqual({ value: 'success' })
    expect(fetchMock).toHaveBeenCalledTimes(3)
    const retryHeaders = new Headers(fetchMock.mock.calls[2][1]?.headers)
    expect(retryHeaders.get('Authorization')).toBe('Bearer new-token')
    expect(fetchMock.mock.calls[1][0]).toContain('/api/auth/refresh')
    expect(fetchMock.mock.calls[1][1]?.credentials).toBe('include')
  })

  it('parses error_code from API errors', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue(
        jsonResponse(
          { error_code: 'REGISTRATION_CLOSED', detail: 'Registration is closed.' },
          409,
        ),
      ),
    )

    await expect(
      apiRequest('/api/example', { skipAuth: true, skipRefresh: true }),
    ).rejects.toMatchObject({
      status: 409,
      errorCode: 'REGISTRATION_CLOSED',
    } satisfies Partial<ApiError>)
  })
})
