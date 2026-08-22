import { apiRequest } from '../../../lib/api/client'
import type { TokenResponse } from '../../../lib/api/types'
import type { RegisterPayload, User } from '../types'

export function loginRequest(email: string, password: string) {
  const body = new URLSearchParams({ username: email, password })

  return apiRequest<TokenResponse>('/api/auth/login', {
    method: 'POST',
    body,
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    skipAuth: true,
    skipRefresh: true,
  })
}

export function registerRequest(payload: RegisterPayload) {
  return apiRequest<User>('/api/auth/register', {
    method: 'POST',
    body: JSON.stringify(payload),
    headers: { 'Content-Type': 'application/json' },
    skipAuth: true,
    skipRefresh: true,
  })
}

export function getCurrentUserRequest() {
  return apiRequest<User>('/api/auth/me')
}

export function logoutRequest() {
  return apiRequest<void>('/api/auth/logout', {
    method: 'POST',
    skipRefresh: true,
  })
}
