export type Role = 'admin' | 'analyst' | 'viewer'
export type InputType = 'name' | 'url' | 'repo'
export type AssessmentStatus = 'pending' | 'confirming' | 'running' | 'complete' | 'failed'
export type RAGStatus = 'red' | 'amber' | 'green'
export type Recommendation = 'approve' | 'conditional' | 'reject'
export type ReviewMode = 'standard' | 'deep_review'
export type Category =
  | 'vendor_trust'
  | 'cve'
  | 'maintenance'
  | 'dependency'
  | 'encryption'
  | 'logging'
  | 'data_exfiltration'
  | 'third_party'
export type AIProvider = 'openwebui' | 'ollama' | 'gemini'

export interface User {
  id: string
  email: string
  full_name: string
  role: Role
  is_active: boolean
}

export interface AssessmentFinding {
  id: string
  assessment_id: string
  category: Category
  score: number
  rag: RAGStatus
  summary: string
  detail: Record<string, unknown>
  analyst_notes: string | null
  edited_by: string | null
  edited_at: string | null
}

export interface AssessmentRun {
  id: string
  run_at: string
  run_by: string
  run_by_name: string | null
  review_mode: ReviewMode
  overall_score: number | null
  overall_rag: RAGStatus | null
  recommendation: Recommendation | null
}

export interface Assessment {
  id: string
  product_name: string
  product_url: string | null
  repo_url: string | null
  input_type: InputType
  status: AssessmentStatus
  review_mode: ReviewMode
  project_scope: string | null
  executive_summary: string | null
  progress_current: number
  progress_total: number
  current_module: string | null
  overall_score: number | null
  overall_rag: RAGStatus | null
  recommendation: Recommendation | null
  submitted_by: string
  submitted_by_name: string | null
  run_started_at: string | null
  created_at: string
  updated_at: string
  findings: AssessmentFinding[]
  runs: AssessmentRun[]
}

export interface AssessmentCreate {
  product_name: string
  product_url?: string
  repo_url?: string
  review_mode: ReviewMode
  project_scope?: string
}

export interface ProductConfirmRequest {
  confirmed_name: string
  confirmed_vendor: string
  confirmed_url: string
}

export interface AIConfig {
  id: string
  provider: AIProvider
  base_url: string
  model_name: string
  is_active: boolean
  has_api_key: boolean
  has_config: boolean
}

export interface AIConfigUpdate {
  base_url?: string
  model_name?: string
  api_key?: string
}

export interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
}

export interface UserCreate {
  email: string
  full_name: string
  password: string
  role: Role
}

export interface UserUpdate {
  full_name?: string
  role?: Role
  is_active?: boolean
}
