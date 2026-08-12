import type { HTMLAttributes, ReactNode } from 'react'
import { colors, radius, spacing } from './tokens'

export interface CardProps extends HTMLAttributes<HTMLDivElement> {
  children: ReactNode
}

export function Card({ children, style, ...props }: CardProps) {
  return (
    <div
      {...props}
      style={{
        background: colors.background,
        border: `1px solid ${colors.border}`,
        borderRadius: radius.md,
        padding: spacing.md,
        ...style,
      }}
    >
      {children}
    </div>
  )
}
