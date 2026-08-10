import type { HTMLAttributes } from 'react'
import { colors, spacing, typography } from './tokens'

export interface SpinnerProps extends HTMLAttributes<HTMLDivElement> {
  label?: string
}

export function Spinner({ label = 'Loading…', style, ...props }: SpinnerProps) {
  return (
    <div
      {...props}
      role="status"
      aria-live="polite"
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: spacing.sm,
        color: colors.textMuted,
        fontFamily: typography.fontFamily,
        fontSize: typography.sizeMd,
        ...style,
      }}
    >
      <svg
        aria-hidden="true"
        width="20"
        height="20"
        viewBox="0 0 24 24"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
      >
        <circle cx="12" cy="12" r="9" stroke={colors.border} strokeWidth="3" />
        <path
          d="M21 12a9 9 0 0 0-9-9"
          stroke={colors.primary}
          strokeWidth="3"
          strokeLinecap="round"
        >
          <animateTransform
            attributeName="transform"
            type="rotate"
            from="0 12 12"
            to="360 12 12"
            dur="0.8s"
            repeatCount="indefinite"
          />
        </path>
      </svg>
      <span>{label}</span>
    </div>
  )
}
