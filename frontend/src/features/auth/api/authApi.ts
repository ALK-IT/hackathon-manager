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

export function verifyEmailRequest(token: string) {
  return apiRequest<{ message: string }>('/api/auth/verify-email', {
    method: 'POST',
    body: JSON.stringify({ token }),
    headers: { 'Content-Type': 'application/json' },
    skipAuth: true,
    skipRefresh: true,
  })
}

export function resendVerificationRequest(email: string) {
  return apiRequest<{ message: string }>('/api/auth/resend-verification', {
    method: 'POST',
    body: JSON.stringify({ email }),
    headers: { 'Content-Type': 'application/json' },
    skipAuth: true,
    skipRefresh: true,
  })
}

export function forgotPasswordRequest(email: string) {
  return apiRequest<{ message: string }>('/api/auth/forgot-password', {
    method: 'POST',
    body: JSON.stringify({ email }),
    headers: { 'Content-Type': 'application/json' },
    skipAuth: true,
    skipRefresh: true,
  })
}

export function resetPasswordRequest(
  token: string,
  password: string,
  confirmPassword: string,
) {
  return apiRequest<{ message: string }>('/api/auth/reset-password', {
    method: 'POST',
    body: JSON.stringify({ token, password, confirm_password: confirmPassword }),
    headers: { 'Content-Type': 'application/json' },
    skipAuth: true,
    skipRefresh: true,
  })
}
