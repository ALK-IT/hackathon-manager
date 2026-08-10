import { useEffect, useMemo, useState, type ReactNode } from 'react'
import {
  getCurrentUserRequest,
  loginRequest,
  logoutRequest,
  registerRequest,
} from '../api/authApi'
import {
  clearAccessToken,
  refreshAccessToken,
  setAccessToken,
} from '../../../lib/api/client'
import type { RegisterPayload, User } from '../types'
import { AuthContext, type AuthContextValue } from './AuthContext'

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    let active = true

    async function restoreSession() {
      try {
        const refreshed = await refreshAccessToken()
        if (!refreshed) return

        const currentUser = await getCurrentUserRequest()
        if (active) setUser(currentUser)
      } catch {
        clearAccessToken()
      } finally {
        if (active) setIsLoading(false)
      }
    }

    void restoreSession()

    return () => {
      active = false
    }
  }, [])

  const value = useMemo<AuthContextValue>(
    () => ({
      user,
      isLoading,
      async login(email, password) {
        const tokens = await loginRequest(email, password)
        setAccessToken(tokens.access_token)

        try {
          setUser(await getCurrentUserRequest())
        } catch (error) {
          clearAccessToken()
          throw error
        }
      },
      async register(payload: RegisterPayload) {
        await registerRequest(payload)
      },
      async logout() {
        try {
          await logoutRequest()
        } catch {
          // Lokalna sesja musi zostać zakończona również przy błędzie sieci.
        } finally {
          clearAccessToken()
          setUser(null)
        }
      },
    }),
    [isLoading, user],
  )

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}
