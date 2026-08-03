import type { HTMLAttributes, ReactNode } from 'react'
import { colors, radius, spacing, typography } from './tokens'

type AlertVariant = 'error' | 'info'

export interface AlertProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
  variant?: AlertVariant
}

const variantStyles: Record<AlertVariant, React.CSSProperties> = {
  error: {
    background: '#fef2f2',
    borderColor: colors.danger,
    color: '#991b1b',
  },
  info: {
    background: '#eff6ff',
    borderColor: colors.primary,
    color: '#1e3a8a',
  },
}

export function Alert({ children, variant = 'info', style, ...props }: AlertProps) {
  return (
    <div
      {...props}
      role={variant === 'error' ? 'alert' : 'status'}
      style={{
        border: '1px solid',
        borderRadius: radius.md,
        padding: spacing.md,
        fontFamily: typography.fontFamily,
        fontSize: typography.sizeMd,
        ...variantStyles[variant],
        ...style,
      }}
    >
      {children}
    </div>
  )
}
