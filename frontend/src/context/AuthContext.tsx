import { createContext, useContext, useState, useCallback } from 'react'
import type { ReactNode } from 'react'

interface AuthUser {
  token: string
}

interface AuthContextValue {
  user: AuthUser | null
  login: (accessToken: string, refreshToken: string) => void
  logout: () => void
  isAuthenticated: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(() => {
    const token = localStorage.getItem('token')
    return token ? { token } : null
  })

  const login = useCallback((accessToken: string, refreshToken: string) => {
    localStorage.setItem('token', accessToken)
    localStorage.setItem('refresh_token', refreshToken)
    setUser({ token: accessToken })
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, login, logout, isAuthenticated: !!user }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuthContext() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuthContext must be used within AuthProvider')
  return ctx
}
