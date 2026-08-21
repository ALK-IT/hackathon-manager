import type { ApiErrorPayload, TokenResponse } from './types'
import { API_URL } from '../../config/env'

let accessToken: string | null = null
let refreshPromise: Promise<boolean> | null = null

export class ApiError extends Error {
  readonly status: number
  readonly errorCode?: string
  readonly validationErrors?: ApiErrorPayload['errors']

  constructor(status: number, payload: ApiErrorPayload = {}) {
    super(payload.detail ?? `Request failed with status ${status}`)
    this.name = 'ApiError'
    this.status = status
    this.errorCode = payload.error_code
    this.validationErrors = payload.errors
  }
}

export function setAccessToken(token: string | null) {
  accessToken = token
}

export function clearAccessToken() {
  accessToken = null
}

async function parseJson(response: Response): Promise<unknown> {
  const contentType = response.headers.get('content-type')
  if (!contentType?.includes('application/json')) return undefined

  try {
    return await response.json()
  } catch {
    return undefined
  }
}

function asErrorPayload(value: unknown): ApiErrorPayload {
  if (!value || typeof value !== 'object') return {}

  const body = value as Record<string, unknown>
  return {
    error_code: typeof body.error_code === 'string' ? body.error_code : undefined,
    detail: typeof body.detail === 'string' ? body.detail : undefined,
    errors: Array.isArray(body.errors) ? (body.errors as ApiErrorPayload['errors']) : undefined,
  }
}

async function refreshAccessTokenRequest(): Promise<boolean> {
  try {
    const response = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      credentials: 'include',
    })

    if (!response.ok) {
      clearAccessToken()
      return false
    }

    const tokens = (await parseJson(response)) as TokenResponse
    setAccessToken(tokens.access_token)
    return true
  } catch {
    clearAccessToken()
    return false
  }
}

export function refreshAccessToken(): Promise<boolean> {
  if (!refreshPromise) {
    refreshPromise = refreshAccessTokenRequest().finally(() => {
      refreshPromise = null
    })
  }

  return refreshPromise
}

interface ApiRequestOptions extends RequestInit {
  skipAuth?: boolean
  skipRefresh?: boolean
}

export async function apiRequest<T>(
  path: string,
  options: ApiRequestOptions = {},
): Promise<T> {
  const { skipAuth = false, skipRefresh = false, headers, ...requestOptions } = options
  const requestHeaders = new Headers(headers)

  if (!skipAuth && accessToken) {
    requestHeaders.set('Authorization', `Bearer ${accessToken}`)
  }

  const response = await fetch(`${API_URL}${path}`, {
    ...requestOptions,
    credentials: 'include',
    headers: requestHeaders,
  })

  if (response.status === 401 && !skipRefresh) {
    const refreshed = await refreshAccessToken()
    if (refreshed) {
      return apiRequest<T>(path, { ...options, skipRefresh: true })
    }
  }

  const body = await parseJson(response)

  if (!response.ok) {
    throw new ApiError(response.status, asErrorPayload(body))
  }

  return body as T
}
