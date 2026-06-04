import client from './client'
import type { AIConfig, AIConfigUpdate, AIProvider } from '../types'

export async function listAIConfigs(): Promise<AIConfig[]> {
  const { data } = await client.get<AIConfig[]>('/ai-config')
  return data
}

export async function upsertAIConfig(provider: AIProvider, body: AIConfigUpdate): Promise<AIConfig> {
  const { data } = await client.put<AIConfig>(`/ai-config/${provider}`, body)
  return data
}

export async function activateAIConfig(provider: AIProvider): Promise<AIConfig> {
  const { data } = await client.post<AIConfig>(`/ai-config/${provider}/activate`)
  return data
}

export async function testAIConnection(): Promise<{ ok: boolean; provider: string; model: string; response: string }> {
  const { data } = await client.post('/ai-config/test')
  return data
}
