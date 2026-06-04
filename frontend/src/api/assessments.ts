import client from './client'
import type { Assessment, AssessmentCreate, ProductConfirmRequest } from '../types'

export async function listAssessments(params?: { status?: string; skip?: number; limit?: number }): Promise<Assessment[]> {
  const { data } = await client.get<Assessment[]>('/assessments', { params })
  return data
}

export async function getAssessment(id: string): Promise<Assessment> {
  const { data } = await client.get<Assessment>(`/assessments/${id}`)
  return data
}

export async function createAssessment(body: AssessmentCreate): Promise<Assessment> {
  const { data } = await client.post<Assessment>('/assessments', body)
  return data
}

export async function confirmProduct(id: string, body: ProductConfirmRequest): Promise<Assessment> {
  const { data } = await client.post<Assessment>(`/assessments/${id}/confirm`, body)
  return data
}

export async function deleteAssessment(id: string): Promise<void> {
  await client.delete(`/assessments/${id}`)
}

export function getPdfUrl(id: string): string {
  return `/api/v1/assessments/${id}/pdf`
}
