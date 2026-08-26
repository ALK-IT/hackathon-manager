import { act, render, screen } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'
import { Countdown } from './Countdown'

describe('Countdown', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    vi.setSystemTime(new Date('2026-08-31T08:57:56Z'))
  })

  afterEach(() => vi.useRealTimers())

  it('counts down to the hackathon start and updates every second', () => {
    render(
      <Countdown
        startDate="2026-09-01T10:00:00Z"
        endDate="2026-09-02T18:00:00Z"
      />,
    )

    expect(screen.getByText('Do rozpoczęcia')).toBeInTheDocument()
    expect(screen.getByRole('timer')).toHaveAccessibleName(
      'Do rozpoczęcia: 1 dni, 1 godzin, 2 minut, 4 sekund',
    )

    act(() => vi.advanceTimersByTime(1000))

    expect(screen.getByRole('timer')).toHaveAccessibleName(
      'Do rozpoczęcia: 1 dni, 1 godzin, 2 minut, 3 sekund',
    )
  })

  it('counts down to the end while the hackathon is running', () => {
    vi.setSystemTime(new Date('2026-09-01T12:00:00Z'))

    render(
      <Countdown
        startDate="2026-09-01T10:00:00Z"
        endDate="2026-09-02T18:00:00Z"
      />,
    )

    expect(screen.getByText('Do zakończenia')).toBeInTheDocument()
    expect(screen.getByRole('timer')).toHaveAccessibleName(
      'Do zakończenia: 1 dni, 6 godzin, 0 minut, 0 sekund',
    )
  })

  it('shows a completed state after the end date', () => {
    vi.setSystemTime(new Date('2026-09-02T18:00:01Z'))

    render(
      <Countdown
        startDate="2026-09-01T10:00:00Z"
        endDate="2026-09-02T18:00:00Z"
      />,
    )

    expect(screen.getByText('Hackathon zakończony')).toBeInTheDocument()
    expect(screen.queryByRole('timer')).not.toBeInTheDocument()
  })

  it('renders nothing when the end date is missing or invalid', () => {
    const { container, rerender } = render(<Countdown endDate={null} />)
    expect(container).toBeEmptyDOMElement()

    rerender(<Countdown endDate="invalid-date" />)
    expect(container).toBeEmptyDOMElement()
  })

  it('clears the timer when unmounted', () => {
    const { unmount } = render(
      <Countdown
        startDate="2026-09-01T10:00:00Z"
        endDate="2026-09-02T18:00:00Z"
      />,
    )

    expect(vi.getTimerCount()).toBe(1)
    unmount()
    expect(vi.getTimerCount()).toBe(0)
  })
})
