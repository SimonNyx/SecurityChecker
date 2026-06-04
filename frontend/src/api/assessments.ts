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

export async function rerunAssessment(id: string, review_mode: 'standard' | 'deep_review'): Promise<Assessment> {
  const { data } = await client.post<Assessment>(`/assessments/${id}/rerun`, { review_mode })
  return data
}

export async function downloadPdf(id: string, productName: string): Promise<void> {
  const { data } = await client.get<Blob>(`/assessments/${id}/pdf`, { responseType: 'blob' })
  const url = URL.createObjectURL(data)
  const a = document.createElement('a')
  a.href = url
  a.download = `security-report-${productName.toLowerCase().replace(/\s+/g, '-')}.pdf`
  a.click()
  URL.revokeObjectURL(url)
}
