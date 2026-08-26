import { useEffect, useState, type HTMLAttributes } from 'react'
import { colors, radius, spacing, typography } from './tokens'

export interface CountdownProps extends HTMLAttributes<HTMLElement> {
  startDate?: string | null
  endDate?: string | null
}

interface RemainingTime {
  days: number
  hours: number
  minutes: number
  seconds: number
}

function parseTimestamp(value: string | null | undefined): number | null {
  if (!value) return null

  const timestamp = new Date(value).getTime()
  return Number.isNaN(timestamp) ? null : timestamp
}

function getRemainingTime(target: number, now: number): RemainingTime {
  const totalSeconds = Math.max(0, Math.ceil((target - now) / 1000))

  return {
    days: Math.floor(totalSeconds / 86_400),
    hours: Math.floor((totalSeconds % 86_400) / 3_600),
    minutes: Math.floor((totalSeconds % 3_600) / 60),
    seconds: totalSeconds % 60,
  }
}

export function Countdown({ startDate, endDate, style, ...props }: CountdownProps) {
  const [now, setNow] = useState(() => Date.now())
  const startTimestamp = parseTimestamp(startDate)
  const endTimestamp = parseTimestamp(endDate)

  useEffect(() => {
    setNow(Date.now())

    if (endTimestamp === null || endTimestamp <= Date.now()) return

    const intervalId = window.setInterval(() => setNow(Date.now()), 1000)
    return () => window.clearInterval(intervalId)
  }, [endTimestamp])

  if (endTimestamp === null) return null

  if (now >= endTimestamp) {
    return (
      <section
        {...props}
        aria-label="Odliczanie czasu hackathonu"
        style={{
          color: colors.textMuted,
          fontFamily: typography.fontFamily,
          ...style,
        }}
      >
        Hackathon zakończony
      </section>
    )
  }

  const isBeforeStart = startTimestamp !== null && now < startTimestamp
  const targetTimestamp = isBeforeStart ? startTimestamp : endTimestamp
  const label = isBeforeStart ? 'Do rozpoczęcia' : 'Do zakończenia'
  const remaining = getRemainingTime(targetTimestamp, now)
  const units = [
    ['dni', remaining.days],
    ['godz.', remaining.hours],
    ['min', remaining.minutes],
    ['sek.', remaining.seconds],
  ] as const

  return (
    <section
      {...props}
      aria-label="Odliczanie czasu hackathonu"
      style={{
        display: 'flex',
        flexDirection: 'column',
        gap: spacing.sm,
        fontFamily: typography.fontFamily,
        ...style,
      }}
    >
      <span style={{ color: colors.textMuted }}>{label}</span>
      <div
        role="timer"
        aria-label={`${label}: ${remaining.days} dni, ${remaining.hours} godzin, ${remaining.minutes} minut, ${remaining.seconds} sekund`}
        style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.sm }}
      >
        {units.map(([unit, value]) => (
          <span
            key={unit}
            style={{
              minWidth: '56px',
              border: `1px solid ${colors.border}`,
              borderRadius: radius.md,
              padding: spacing.sm,
              textAlign: 'center',
            }}
          >
            <strong style={{ display: 'block', fontSize: typography.sizeLg }}>{value}</strong>
            <span style={{ color: colors.textMuted, fontSize: typography.sizeSm }}>{unit}</span>
          </span>
        ))}
      </div>
    </section>
  )
}
