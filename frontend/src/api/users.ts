import client from './client'
import type { User, UserCreate, UserUpdate } from '../types'

export async function listUsers(): Promise<User[]> {
  const { data } = await client.get<User[]>('/users')
  return data
}

export async function createUser(body: UserCreate): Promise<User> {
  const { data } = await client.post<User>('/users', body)
  return data
}

export async function updateUser(id: string, body: UserUpdate): Promise<User> {
  const { data } = await client.patch<User>(`/users/${id}`, body)
  return data
}
