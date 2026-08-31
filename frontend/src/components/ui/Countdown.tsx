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

type PolishUnitForms = readonly [singular: string, paucal: string, plural: string]

function inflectPolishUnit(value: number, [singular, paucal, plural]: PolishUnitForms): string {
  if (value === 1) return singular

  const lastDigit = value % 10
  const lastTwoDigits = value % 100
  if (lastDigit >= 2 && lastDigit <= 4 && (lastTwoDigits < 12 || lastTwoDigits > 14)) {
    return paucal
  }

  return plural
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
    if (endTimestamp === null || endTimestamp <= Date.now()) return

    const intervalId = window.setInterval(() => {
      const currentTime = Date.now()
      setNow(currentTime)

      if (currentTime >= endTimestamp) {
        window.clearInterval(intervalId)
      }
    }, 1000)

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
    ['days', remaining.days, inflectPolishUnit(remaining.days, ['dzień', 'dni', 'dni'])],
    [
      'hours',
      remaining.hours,
      inflectPolishUnit(remaining.hours, ['godzina', 'godziny', 'godzin']),
    ],
    [
      'minutes',
      remaining.minutes,
      inflectPolishUnit(remaining.minutes, ['minuta', 'minuty', 'minut']),
    ],
    [
      'seconds',
      remaining.seconds,
      inflectPolishUnit(remaining.seconds, ['sekunda', 'sekundy', 'sekund']),
    ],
  ] as const
  const accessibleRemainingTime = units
    .map(([, value, unit]) => `${value} ${unit}`)
    .join(', ')

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
        aria-label={`${label}: ${accessibleRemainingTime}`}
        style={{ display: 'flex', flexWrap: 'wrap', gap: spacing.sm }}
      >
        {units.map(([key, value, unit]) => (
          <span
            key={key}
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
