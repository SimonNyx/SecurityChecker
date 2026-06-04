import client from './client'
import type { AIConfig, AIConfigUpdate } from '../types'

export async function getAIConfig(): Promise<AIConfig> {
  const { data } = await client.get<AIConfig>('/ai-config')
  return data
}

export async function updateAIConfig(body: AIConfigUpdate): Promise<AIConfig> {
  const { data } = await client.put<AIConfig>('/ai-config', body)
  return data
}
