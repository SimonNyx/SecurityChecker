import axios from 'axios'
import type { AxiosError } from 'axios'

const client = axios.create({ baseURL: '/api/v1' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

let refreshing = false

client.interceptors.response.use(
  (r) => r,
  async (error: AxiosError) => {
    const original = error.config as typeof error.config & { _retry?: boolean }
    if (
      error.response?.status === 401 &&
      !original?._retry &&
      !original?.url?.includes('/auth/') &&
      !refreshing
    ) {
      original._retry = true
      refreshing = true
      const refreshToken = localStorage.getItem('refresh_token')
      if (refreshToken) {
        try {
          const { data } = await axios.post('/api/v1/auth/refresh', { refresh_token: refreshToken })
          localStorage.setItem('token', data.access_token)
          localStorage.setItem('refresh_token', data.refresh_token)
          if (original?.headers) original.headers['Authorization'] = `Bearer ${data.access_token}`
          refreshing = false
          return client(original!)
        } catch {
          // refresh failed — fall through to logout
        }
      }
      refreshing = false
      localStorage.removeItem('token')
      localStorage.removeItem('refresh_token')
      window.location.pathname = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
