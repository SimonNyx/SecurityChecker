import { createContext, useContext, useState, useCallback, useEffect } from 'react'
import type { ReactNode } from 'react'
import type { User } from '../types'
import client from '../api/client'

interface AuthContextValue {
  currentUser: User | null
  isAuthenticated: boolean
  login: (accessToken: string, refreshToken: string) => void
  logout: () => void
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [currentUser, setCurrentUser] = useState<User | null>(null)
  const [ready, setReady] = useState(false)

  const fetchMe = useCallback(async () => {
    try {
      const { data } = await client.get<User>('/auth/me')
      setCurrentUser(data)
    } catch {
      setCurrentUser(null)
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
    } finally {
      setReady(true)
    }
  }, [])

  useEffect(() => {
    if (localStorage.getItem('token')) {
      fetchMe()
    } else {
      setReady(true)
    }
  }, [fetchMe])

  const login = useCallback(async (accessToken: string, refreshToken: string) => {
    localStorage.setItem('token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    await fetchMe()
  }, [fetchMe])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    setCurrentUser(null)
  }, [])

  if (!ready) return null

  return (
    <AuthContext.Provider value={{ currentUser, isAuthenticated: !!currentUser, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider')
  return ctx
}
