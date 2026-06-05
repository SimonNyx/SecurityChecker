import client from './client'
import type { APIKey } from '../types'

export async function listAPIKeys(): Promise<APIKey[]> {
  const { data } = await client.get<APIKey[]>('/auth/api-keys')
  return data
}

export async function createAPIKey(name: string, expires_in_days: number): Promise<APIKey> {
  const { data } = await client.post<APIKey>('/auth/api-keys', { name, expires_in_days })
  return data
}

export async function revokeAPIKey(id: string): Promise<void> {
  await client.delete(`/auth/api-keys/${id}`)
}
