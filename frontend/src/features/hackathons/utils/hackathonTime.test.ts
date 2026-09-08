import { describe, expect, it } from 'vitest'
import { isHackathonInProgress } from './hackathonTime'

describe('isHackathonInProgress', () => {
  const start = '2026-09-08T10:00:00Z'
  const end = '2026-09-08T18:00:00Z'

  it('returns true from the start until the end of the hackathon', () => {
    expect(isHackathonInProgress(start, end, Date.parse(start))).toBe(true)
    expect(
      isHackathonInProgress(start, end, Date.parse('2026-09-08T17:59:59Z')),
    ).toBe(true)
  })

  it('returns false before the start, at the end and for invalid dates', () => {
    expect(
      isHackathonInProgress(start, end, Date.parse('2026-09-08T09:59:59Z')),
    ).toBe(false)
    expect(isHackathonInProgress(start, end, Date.parse(end))).toBe(false)
    expect(isHackathonInProgress('invalid', end)).toBe(false)
  })
})
