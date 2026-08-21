import type { ReactNode } from 'react'
import { Navigate } from 'react-router-dom'
import { useAuth } from '../../features/auth'

export function AdminRoute({ children }: { children: ReactNode }) {
  const { user } = useAuth()

  if (user?.role !== 'admin') return <Navigate to="/hackathons" replace />
  return children
}
