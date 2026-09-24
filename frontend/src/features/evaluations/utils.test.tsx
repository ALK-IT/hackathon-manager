import { act, renderHook } from '@testing-library/react'
import { afterEach, expect, it, vi } from 'vitest'
import { ApiError } from '../../lib/api/client'
import { evaluationError, useHasEnded } from './utils'

afterEach(() => vi.useRealTimers())

it('changes to ended locally at the deadline', () => {
  vi.useFakeTimers()
  const now = Date.now()
  const { result } = renderHook(() => useHasEnded(new Date(now + 2000).toISOString()))
  expect(result.current).toBe(false)
  act(() => vi.advanceTimersByTime(2000))
  expect(result.current).toBe(true)
})

it('maps task permission errors without exposing server details', () => {
  expect(evaluationError(new ApiError(403, { error_code: 'TASK_PERMISSION_DENIED', detail: 'private' })))
    .toBe('Nie masz uprawnień do przeglądania lub oceniania tych rozwiązań.')
})
