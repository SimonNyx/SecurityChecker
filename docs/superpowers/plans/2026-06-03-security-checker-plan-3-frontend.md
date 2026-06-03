# SecurityChecker — Plan 3: Frontend

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the React + TypeScript SPA with all 7 screens (login, dashboard, new assessment, product confirmation, assessment detail, admin users, admin AI config) served via Nginx with `/api/` proxied to the backend.

**Architecture:** React 18 SPA with React Router v6 for routing, React Query for server state, Axios for HTTP with JWT interceptor, TypeScript throughout. Nginx serves the built SPA and proxies `/api/` to the FastAPI container. No SSR.

**Tech Stack:** React 18, TypeScript, Vite, React Router v6, TanStack Query v5, Axios, Tailwind CSS.

**Prerequisite plan:** Plan 1 (Foundation) must be complete — the frontend talks to the API.

---

## File Map

```
frontend/
├── Dockerfile
├── nginx.conf
├── package.json
├── tsconfig.json
├── vite.config.ts
├── tailwind.config.js
├── postcss.config.js
└── src/
    ├── main.tsx
    ├── App.tsx
    ├── types/index.ts           # TypeScript types matching API schemas
    ├── api/
    │   ├── client.ts            # Axios instance + JWT interceptor
    │   ├── assessments.ts       # Assessment API calls
    │   ├── users.ts             # User API calls
    │   └── aiConfig.ts          # AI Config API calls
    ├── auth/
    │   ├── AuthContext.tsx      # Login state, current user, logout
    │   └── ProtectedRoute.tsx   # Redirects unauthenticated users
    ├── components/
    │   ├── Layout.tsx           # Sidebar + main content shell
    │   ├── RAGBadge.tsx         # Green/amber/red coloured pill
    │   ├── ScoreBar.tsx         # Score bar with colour fill
    │   ├── FindingCard.tsx      # Module finding card
    │   └── AssessmentTable.tsx  # Dashboard table
    └── pages/
        ├── LoginPage.tsx
        ├── DashboardPage.tsx
        ├── NewAssessmentPage.tsx
        ├── ProductConfirmationPage.tsx
        ├── AssessmentDetailPage.tsx
        └── admin/
            ├── UsersPage.tsx
            └── AIConfigPage.tsx
```

---

### Task 19: Frontend scaffold

**Files:**
- Create: `frontend/Dockerfile`
- Create: `frontend/nginx.conf`
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/tailwind.config.js`
- Create: `frontend/postcss.config.js`
- Create: `frontend/src/main.tsx`
- Create: `frontend/src/App.tsx`

- [ ] **Step 1: Create `frontend/package.json`**

```json
{
  "name": "securitychecker-frontend",
  "private": true,
  "version": "1.0.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.1",
    "react-dom": "^18.3.1",
    "react-router-dom": "^6.26.2",
    "@tanstack/react-query": "^5.56.2",
    "axios": "^1.7.7"
  },
  "devDependencies": {
    "@types/react": "^18.3.5",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.1",
    "autoprefixer": "^10.4.20",
    "postcss": "^8.4.45",
    "tailwindcss": "^3.4.10",
    "typescript": "^5.5.3",
    "vite": "^5.4.6"
  }
}
```

- [ ] **Step 2: Create `frontend/tsconfig.json`**

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "baseUrl": ".",
    "paths": { "@/*": ["src/*"] }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

- [ ] **Step 3: Create `frontend/tsconfig.node.json`**

```json
{
  "compilerOptions": {
    "composite": true,
    "skipLibCheck": true,
    "module": "ESNext",
    "moduleResolution": "bundler",
    "allowSyntheticDefaultImports": true
  },
  "include": ["vite.config.ts"]
}
```

- [ ] **Step 4: Create `frontend/vite.config.ts`**

```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import path from 'path'

export default defineConfig({
  plugins: [react()],
  resolve: { alias: { '@': path.resolve(__dirname, 'src') } },
  server: {
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})
```

- [ ] **Step 5: Create `frontend/tailwind.config.js`**

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{ts,tsx}'],
  theme: {
    extend: {
      colors: {
        green: { DEFAULT: '#2d8a3e', light: '#d4edda' },
        amber: { DEFAULT: '#b86200', light: '#fff3cd' },
        red: { DEFAULT: '#c0392b', light: '#f8d7da' },
        brand: { DEFAULT: '#1a3a5c', light: '#4a9eff' },
      },
    },
  },
  plugins: [],
}
```

- [ ] **Step 6: Create `frontend/postcss.config.js`**

```javascript
export default {
  plugins: { tailwindcss: {}, autoprefixer: {} },
}
```

- [ ] **Step 7: Create `frontend/nginx.conf`**

```nginx
server {
    listen 80;
    root /usr/share/nginx/html;
    index index.html;

    location /api/ {
        proxy_pass http://api:8000/api/;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location / {
        try_files $uri $uri/ /index.html;
    }
}
```

- [ ] **Step 8: Create `frontend/Dockerfile`**

```dockerfile
FROM node:20-alpine AS build
WORKDIR /app
COPY package.json .
RUN npm install
COPY . .
RUN npm run build

FROM nginx:alpine
COPY --from=build /app/dist /usr/share/nginx/html
COPY nginx.conf /etc/nginx/conf.d/default.conf
EXPOSE 80
```

- [ ] **Step 9: Create `frontend/index.html`**

```html
<!DOCTYPE html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>SecurityChecker</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 10: Create `frontend/src/main.tsx`**

```typescript
import React from 'react'
import ReactDOM from 'react-dom/client'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import App from './App'
import './index.css'

const queryClient = new QueryClient({
  defaultOptions: { queries: { staleTime: 30_000, retry: 1 } },
})

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <QueryClientProvider client={queryClient}>
      <App />
    </QueryClientProvider>
  </React.StrictMode>
)
```

- [ ] **Step 11: Create `frontend/src/index.css`**

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

body { @apply bg-gray-950 text-gray-100 min-h-screen; }
```

- [ ] **Step 12: Create stub `frontend/src/App.tsx`** (will be replaced in Task 20)

```typescript
export default function App() {
  return <div className="p-8 text-white">SecurityChecker loading...</div>
}
```

- [ ] **Step 13: Verify dev build runs**

```bash
cd frontend && npm install && npm run build
```

Expected: Build succeeds with no TypeScript errors.

- [ ] **Step 14: Commit**

```bash
git add frontend/
git commit -m "feat: frontend scaffold (Vite, React 18, Tailwind, Nginx)"
```

---

### Task 20: TypeScript types and API client

**Files:**
- Create: `frontend/src/types/index.ts`
- Create: `frontend/src/api/client.ts`
- Create: `frontend/src/api/assessments.ts`
- Create: `frontend/src/api/users.ts`
- Create: `frontend/src/api/aiConfig.ts`

- [ ] **Step 1: Create `frontend/src/types/index.ts`**

```typescript
export type Role = 'admin' | 'analyst' | 'viewer'
export type RAGStatus = 'red' | 'amber' | 'green'
export type AssessmentStatus = 'pending' | 'confirming' | 'running' | 'complete' | 'failed'
export type ReviewMode = 'standard' | 'deep_review'
export type Recommendation = 'approve' | 'conditional' | 'reject'
export type Category =
  | 'vendor_trust' | 'cve' | 'maintenance' | 'dependency'
  | 'encryption' | 'logging' | 'data_exfiltration' | 'third_party'
export type AIProvider = 'openwebui' | 'ollama' | 'gemini'

export interface User {
  id: string
  email: string
  full_name: string
  role: Role
  is_active: boolean
  created_at: string
}

export interface Assessment {
  id: string
  product_name: string
  product_url: string | null
  repo_url: string | null
  input_type: 'name' | 'url' | 'repo'
  status: AssessmentStatus
  review_mode: ReviewMode
  overall_score: number | null
  overall_rag: RAGStatus | null
  recommendation: Recommendation | null
  submitted_by: string
  created_at: string
  updated_at: string
}

export interface Finding {
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

export interface AIConfig {
  id: string
  provider: AIProvider
  base_url: string
  model_name: string
  is_active: boolean
}

export interface TokenResponse {
  access_token: string
  token_type: string
}
```

- [ ] **Step 2: Create `frontend/src/api/client.ts`**

```typescript
import axios from 'axios'

const client = axios.create({ baseURL: '/api/v1' })

client.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

client.interceptors.response.use(
  (r) => r,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default client
```

- [ ] **Step 3: Create `frontend/src/api/assessments.ts`**

```typescript
import client from './client'
import type { Assessment, Finding, ReviewMode } from '@/types'

export interface CreateAssessmentInput {
  product_name: string
  product_url?: string
  repo_url?: string
  review_mode: ReviewMode
}

export interface ConfirmProductInput {
  confirmed_name: string
  confirmed_vendor: string
  confirmed_url: string
}

export interface UpdateFindingInput {
  analyst_notes?: string
  score?: number
}

export const assessmentsApi = {
  list: (params?: { status_filter?: string; skip?: number; limit?: number }) =>
    client.get<Assessment[]>('/assessments', { params }).then((r) => r.data),

  get: (id: string) =>
    client.get<Assessment>(`/assessments/${id}`).then((r) => r.data),

  create: (input: CreateAssessmentInput) =>
    client.post<Assessment>('/assessments', input).then((r) => r.data),

  confirmProduct: (id: string, input: ConfirmProductInput) =>
    client.post<Assessment>(`/assessments/${id}/confirm-product`, input).then((r) => r.data),

  updateFinding: (assessmentId: string, category: string, input: UpdateFindingInput) =>
    client.put<Finding>(`/assessments/${assessmentId}/findings/${category}`, input).then((r) => r.data),

  pdfUrl: (id: string) => `/api/v1/assessments/${id}/pdf`,
}
```

- [ ] **Step 4: Create `frontend/src/api/users.ts`**

```typescript
import client from './client'
import type { User, Role } from '@/types'

export interface CreateUserInput {
  email: string
  password: string
  full_name: string
  role: Role
}

export interface UpdateUserInput {
  full_name?: string
  role?: Role
  is_active?: boolean
}

export const usersApi = {
  list: () => client.get<User[]>('/users').then((r) => r.data),
  create: (input: CreateUserInput) => client.post<User>('/users', input).then((r) => r.data),
  update: (id: string, input: UpdateUserInput) =>
    client.put<User>(`/users/${id}`, input).then((r) => r.data),
}
```

- [ ] **Step 5: Create `frontend/src/api/aiConfig.ts`**

```typescript
import client from './client'
import type { AIConfig, AIProvider } from '@/types'

export interface UpdateAIConfigInput {
  provider?: AIProvider
  base_url?: string
  api_key?: string
  model_name?: string
}

export const aiConfigApi = {
  get: () => client.get<AIConfig>('/ai-config').then((r) => r.data),
  update: (input: UpdateAIConfigInput) =>
    client.put<AIConfig>('/ai-config', input).then((r) => r.data),
}
```

- [ ] **Step 6: Verify TypeScript compiles**

```bash
cd frontend && npm run build
```

Expected: No TypeScript errors.

- [ ] **Step 7: Commit**

```bash
git add frontend/src/types/ frontend/src/api/
git commit -m "feat: TypeScript types and API client layer"
```

---

### Task 21: Auth context and protected routes

**Files:**
- Create: `frontend/src/auth/AuthContext.tsx`
- Create: `frontend/src/auth/ProtectedRoute.tsx`
- Create: `frontend/src/pages/LoginPage.tsx`
- Modify: `frontend/src/App.tsx`

- [ ] **Step 1: Create `frontend/src/auth/AuthContext.tsx`**

```typescript
import { createContext, useContext, useState, useCallback, ReactNode } from 'react'
import client from '@/api/client'
import type { User } from '@/types'

interface AuthContextType {
  user: User | null
  token: string | null
  login: (email: string, password: string) => Promise<void>
  logout: () => void
  isLoading: boolean
}

const AuthContext = createContext<AuthContextType | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem('token'))
  const [user, setUser] = useState<User | null>(null)
  const [isLoading, setIsLoading] = useState(false)

  const login = useCallback(async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const { data } = await client.post<{ access_token: string }>('/auth/login', { email, password })
      localStorage.setItem('token', data.access_token)
      setToken(data.access_token)

      // Decode user info from JWT payload (base64)
      const payload = JSON.parse(atob(data.access_token.split('.')[1]))
      setUser({ id: payload.sub, role: payload.role } as User)
    } finally {
      setIsLoading(false)
    }
  }, [])

  const logout = useCallback(() => {
    localStorage.removeItem('token')
    setToken(null)
    setUser(null)
  }, [])

  return (
    <AuthContext.Provider value={{ user, token, login, logout, isLoading }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
```

- [ ] **Step 2: Create `frontend/src/auth/ProtectedRoute.tsx`**

```typescript
import { Navigate } from 'react-router-dom'
import { useAuth } from './AuthContext'
import type { Role } from '@/types'

interface Props {
  children: React.ReactNode
  minimumRole?: Role
}

const ROLE_ORDER: Record<Role, number> = { viewer: 0, analyst: 1, admin: 2 }

export function ProtectedRoute({ children, minimumRole = 'viewer' }: Props) {
  const { token, user } = useAuth()
  if (!token) return <Navigate to="/login" replace />
  if (minimumRole && user && ROLE_ORDER[user.role] < ROLE_ORDER[minimumRole]) {
    return <Navigate to="/" replace />
  }
  return <>{children}</>
}
```

- [ ] **Step 3: Create `frontend/src/pages/LoginPage.tsx`**

```typescript
import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'

export default function LoginPage() {
  const { login } = useAuth()
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      await login(email, password)
      navigate('/')
    } catch {
      setError('Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-950">
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-8 w-full max-w-sm">
        <h1 className="text-xl font-bold text-white mb-1">🔐 SecurityChecker</h1>
        <p className="text-gray-400 text-sm mb-6">Sign in to your account</p>
        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Email</label>
            <input
              type="email" value={email} onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Password</label>
            <input
              type="password" value={password} onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-white text-sm focus:outline-none focus:border-blue-500"
            />
          </div>
          {error && <p className="text-red-400 text-xs">{error}</p>}
          <button
            type="submit" disabled={loading}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg text-sm disabled:opacity-50"
          >
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>
      </div>
    </div>
  )
}
```

- [ ] **Step 4: Replace `frontend/src/App.tsx`**

```typescript
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom'
import { AuthProvider } from '@/auth/AuthContext'
import { ProtectedRoute } from '@/auth/ProtectedRoute'
import LoginPage from '@/pages/LoginPage'
import DashboardPage from '@/pages/DashboardPage'
import NewAssessmentPage from '@/pages/NewAssessmentPage'
import ProductConfirmationPage from '@/pages/ProductConfirmationPage'
import AssessmentDetailPage from '@/pages/AssessmentDetailPage'
import UsersPage from '@/pages/admin/UsersPage'
import AIConfigPage from '@/pages/admin/AIConfigPage'

// Stub pages — replaced in subsequent tasks
const Stub = ({ name }: { name: string }) => <div className="p-8 text-white">{name}</div>

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />
          <Route path="/" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/assessments/new" element={<ProtectedRoute minimumRole="analyst"><NewAssessmentPage /></ProtectedRoute>} />
          <Route path="/assessments/:id/confirm" element={<ProtectedRoute minimumRole="analyst"><ProductConfirmationPage /></ProtectedRoute>} />
          <Route path="/assessments/:id" element={<ProtectedRoute><AssessmentDetailPage /></ProtectedRoute>} />
          <Route path="/admin/users" element={<ProtectedRoute minimumRole="admin"><UsersPage /></ProtectedRoute>} />
          <Route path="/admin/ai-config" element={<ProtectedRoute minimumRole="admin"><AIConfigPage /></ProtectedRoute>} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  )
}
```

Create stub page files so the build succeeds:

```bash
mkdir -p frontend/src/pages/admin
```

Create `frontend/src/pages/DashboardPage.tsx`:
```typescript
export default function DashboardPage() { return <div className="p-8 text-white">Dashboard</div> }
```

Create `frontend/src/pages/NewAssessmentPage.tsx`:
```typescript
export default function NewAssessmentPage() { return <div className="p-8 text-white">New Assessment</div> }
```

Create `frontend/src/pages/ProductConfirmationPage.tsx`:
```typescript
export default function ProductConfirmationPage() { return <div className="p-8 text-white">Confirm Product</div> }
```

Create `frontend/src/pages/AssessmentDetailPage.tsx`:
```typescript
export default function AssessmentDetailPage() { return <div className="p-8 text-white">Assessment Detail</div> }
```

Create `frontend/src/pages/admin/UsersPage.tsx`:
```typescript
export default function UsersPage() { return <div className="p-8 text-white">Users</div> }
```

Create `frontend/src/pages/admin/AIConfigPage.tsx`:
```typescript
export default function AIConfigPage() { return <div className="p-8 text-white">AI Config</div> }
```

- [ ] **Step 5: Verify build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds.

- [ ] **Step 6: Commit**

```bash
git add frontend/src/
git commit -m "feat: auth context, protected routes, login page, routing"
```

---

### Task 22: Layout and shared components

**Files:**
- Create: `frontend/src/components/Layout.tsx`
- Create: `frontend/src/components/RAGBadge.tsx`
- Create: `frontend/src/components/ScoreBar.tsx`
- Create: `frontend/src/components/FindingCard.tsx`

- [ ] **Step 1: Create `frontend/src/components/RAGBadge.tsx`**

```typescript
import type { RAGStatus, Recommendation } from '@/types'

const RECOMMENDATION_LABELS: Record<Recommendation, string> = {
  approve: 'Approve',
  conditional: 'Conditional',
  reject: 'Reject',
}

const RAG_STYLES: Record<RAGStatus, string> = {
  green: 'bg-green-100 text-green-800 border border-green-300',
  amber: 'bg-amber-100 text-amber-800 border border-amber-300',
  red: 'bg-red-100 text-red-800 border border-red-300',
}

export function RAGBadge({ rag, recommendation }: { rag: RAGStatus; recommendation?: Recommendation }) {
  const label = recommendation ? RECOMMENDATION_LABELS[recommendation] : rag.toUpperCase()
  return (
    <span className={`inline-flex items-center gap-1 px-2.5 py-0.5 rounded-full text-xs font-semibold ${RAG_STYLES[rag]}`}>
      <span className="w-1.5 h-1.5 rounded-full bg-current" />
      {label}
    </span>
  )
}
```

- [ ] **Step 2: Create `frontend/src/components/ScoreBar.tsx`**

```typescript
import type { RAGStatus } from '@/types'

const BAR_COLOURS: Record<RAGStatus, string> = {
  green: 'bg-green-500',
  amber: 'bg-amber-500',
  red: 'bg-red-500',
}

const SCORE_COLOURS: Record<RAGStatus, string> = {
  green: 'text-green-400',
  amber: 'text-amber-400',
  red: 'text-red-400',
}

export function ScoreBar({ score, rag }: { score: number; rag: RAGStatus }) {
  return (
    <div className="flex items-center gap-3">
      <div className="flex-1 bg-gray-700 rounded-full h-1.5">
        <div
          className={`h-1.5 rounded-full ${BAR_COLOURS[rag]}`}
          style={{ width: `${(score / 10) * 100}%` }}
        />
      </div>
      <span className={`text-sm font-bold w-8 text-right ${SCORE_COLOURS[rag]}`}>
        {score.toFixed(1)}
      </span>
    </div>
  )
}
```

- [ ] **Step 3: Create `frontend/src/components/FindingCard.tsx`**

```typescript
import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import type { Finding } from '@/types'
import { RAGBadge } from './RAGBadge'
import { ScoreBar } from './ScoreBar'
import { assessmentsApi } from '@/api/assessments'

const CATEGORY_LABELS: Record<string, string> = {
  vendor_trust: '🏢 Vendor Trust',
  cve: '🛡️ CVE History',
  maintenance: '🔧 Maintenance',
  dependency: '📦 Dependencies',
  encryption: '🔒 Encryption',
  logging: '📊 Logging',
  data_exfiltration: '📡 Data Exfiltration',
  third_party: '🔗 Third-party',
}

interface Props {
  finding: Finding
  canEdit: boolean
}

export function FindingCard({ finding, canEdit }: Props) {
  const [notes, setNotes] = useState(finding.analyst_notes ?? '')
  const [editing, setEditing] = useState(false)
  const qc = useQueryClient()

  const mutation = useMutation({
    mutationFn: () =>
      assessmentsApi.updateFinding(finding.assessment_id, finding.category, { analyst_notes: notes }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assessment', finding.assessment_id] })
      setEditing(false)
    },
  })

  const ragBorderColour = { green: 'border-green-700', amber: 'border-amber-700', red: 'border-red-700' }[finding.rag]

  return (
    <div className={`bg-gray-900 border ${ragBorderColour} rounded-xl p-4`}>
      <div className="flex justify-between items-start mb-2">
        <span className="font-semibold text-sm">{CATEGORY_LABELS[finding.category] ?? finding.category}</span>
        <RAGBadge rag={finding.rag} />
      </div>
      <ScoreBar score={finding.score} rag={finding.rag} />
      <p className="text-gray-400 text-xs mt-2 leading-relaxed">{finding.summary}</p>
      {canEdit && (
        <div className="mt-3">
          {editing ? (
            <div className="space-y-2">
              <textarea
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                rows={3}
                placeholder="Add analyst notes..."
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-xs text-white resize-none focus:outline-none focus:border-blue-500"
              />
              <div className="flex gap-2">
                <button
                  onClick={() => mutation.mutate()}
                  className="text-xs bg-blue-600 hover:bg-blue-700 text-white px-3 py-1 rounded-lg"
                >
                  Save
                </button>
                <button onClick={() => setEditing(false)} className="text-xs text-gray-400 hover:text-white">
                  Cancel
                </button>
              </div>
            </div>
          ) : (
            <button onClick={() => setEditing(true)} className="text-xs text-blue-400 hover:text-blue-300">
              {notes ? '✏️ Edit notes' : '+ Add notes'}
            </button>
          )}
          {notes && !editing && (
            <p className="text-xs text-gray-300 mt-1 italic">{notes}</p>
          )}
        </div>
      )}
    </div>
  )
}
```

- [ ] **Step 4: Create `frontend/src/components/Layout.tsx`**

```typescript
import { NavLink, useNavigate } from 'react-router-dom'
import { useAuth } from '@/auth/AuthContext'
import type { Role } from '@/types'

const ROLE_ORDER: Record<Role, number> = { viewer: 0, analyst: 1, admin: 2 }

function NavItem({ to, label, minRole, userRole }: { to: string; label: string; minRole?: Role; userRole: Role }) {
  if (minRole && ROLE_ORDER[userRole] < ROLE_ORDER[minRole]) return null
  return (
    <NavLink
      to={to}
      className={({ isActive }) =>
        `block px-4 py-2 text-sm rounded-lg transition-colors ${
          isActive ? 'bg-blue-600/20 text-blue-400 font-semibold' : 'text-gray-400 hover:text-white hover:bg-gray-800'
        }`
      }
    >
      {label}
    </NavLink>
  )
}

export function Layout({ children }: { children: React.ReactNode }) {
  const { user, logout } = useAuth()
  const navigate = useNavigate()

  function handleLogout() {
    logout()
    navigate('/login')
  }

  const role = user?.role ?? 'viewer'

  return (
    <div className="flex min-h-screen bg-gray-950">
      <aside className="w-56 flex-shrink-0 bg-gray-900 border-r border-gray-800 flex flex-col py-4 px-3">
        <div className="text-blue-400 font-bold text-sm px-1 mb-6">🔐 SecurityChecker</div>
        <nav className="flex-1 space-y-1">
          <NavItem to="/" label="📋 Assessments" userRole={role} />
          <NavItem to="/assessments/new" label="➕ New Assessment" minRole="analyst" userRole={role} />
          <div className="pt-3 pb-1 px-1 text-xs text-gray-600 uppercase tracking-wider">Admin</div>
          <NavItem to="/admin/users" label="👥 Users" minRole="admin" userRole={role} />
          <NavItem to="/admin/ai-config" label="🤖 AI Config" minRole="admin" userRole={role} />
        </nav>
        <div className="border-t border-gray-800 pt-3 px-1">
          <div className="text-xs text-gray-500 mb-1">{user?.id?.slice(0, 8)}…</div>
          <div className="text-xs text-amber-400 uppercase font-semibold mb-2">{role}</div>
          <button onClick={handleLogout} className="text-xs text-gray-500 hover:text-white">
            Sign out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-auto p-6">{children}</main>
    </div>
  )
}
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/components/
git commit -m "feat: Layout, RAGBadge, ScoreBar, FindingCard components"
```

---

### Task 23: Dashboard page

**Files:**
- Replace: `frontend/src/pages/DashboardPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/DashboardPage.tsx`**

```typescript
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { RAGBadge } from '@/components/RAGBadge'
import { assessmentsApi } from '@/api/assessments'
import type { Assessment } from '@/types'

function StatusPill({ status }: { status: Assessment['status'] }) {
  const map: Record<Assessment['status'], string> = {
    pending: 'bg-gray-700 text-gray-300',
    confirming: 'bg-purple-900/40 text-purple-300',
    running: 'bg-blue-900/40 text-blue-300',
    complete: 'bg-green-900/40 text-green-300',
    failed: 'bg-red-900/40 text-red-300',
  }
  return (
    <span className={`px-2 py-0.5 rounded-full text-xs font-medium ${map[status]}`}>
      {status}
    </span>
  )
}

export default function DashboardPage() {
  const [statusFilter, setStatusFilter] = useState<string>('')
  const [search, setSearch] = useState('')

  const { data: assessments = [], isLoading } = useQuery({
    queryKey: ['assessments', statusFilter],
    queryFn: () => assessmentsApi.list({ status_filter: statusFilter || undefined }),
  })

  const filtered = assessments.filter((a) =>
    a.product_name.toLowerCase().includes(search.toLowerCase())
  )

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <div>
          <h1 className="text-xl font-bold text-white">Assessments</h1>
          <p className="text-gray-500 text-sm">{assessments.length} total</p>
        </div>
        <Link
          to="/assessments/new"
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg"
        >
          + New Assessment
        </Link>
      </div>

      {/* Filters */}
      <div className="flex flex-wrap gap-2 mb-4">
        {(['', 'complete', 'running', 'pending', 'failed'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s)}
            className={`px-3 py-1 rounded-full text-xs font-medium border transition-colors ${
              statusFilter === s
                ? 'bg-blue-600 border-blue-600 text-white'
                : 'border-gray-700 text-gray-400 hover:border-gray-500'
            }`}
          >
            {s || 'All'}
          </button>
        ))}
        <input
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          placeholder="Search product…"
          className="ml-auto bg-gray-800 border border-gray-700 rounded-lg px-3 py-1 text-xs text-white focus:outline-none focus:border-blue-500 w-44"
        />
      </div>

      {/* Table */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3 text-left">Product</th>
              <th className="px-4 py-3 text-left">Score</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3 text-left">Mode</th>
              <th className="px-4 py-3 text-left">Date</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">Loading…</td></tr>
            )}
            {!isLoading && filtered.length === 0 && (
              <tr><td colSpan={6} className="px-4 py-8 text-center text-gray-500">No assessments found.</td></tr>
            )}
            {filtered.map((a) => (
              <tr key={a.id} className="border-t border-gray-800 hover:bg-gray-800/50 transition-colors">
                <td className="px-4 py-3">
                  <div className="font-medium text-white">{a.product_name}</div>
                  {a.product_url && (
                    <div className="text-xs text-gray-500 truncate max-w-[180px]">{a.product_url}</div>
                  )}
                </td>
                <td className="px-4 py-3">
                  {a.overall_score != null ? (
                    <span className={`font-bold ${a.overall_rag === 'green' ? 'text-green-400' : a.overall_rag === 'amber' ? 'text-amber-400' : 'text-red-400'}`}>
                      {a.overall_score.toFixed(1)}
                    </span>
                  ) : (
                    <span className="text-gray-600">—</span>
                  )}
                </td>
                <td className="px-4 py-3">
                  {a.overall_rag && a.recommendation ? (
                    <RAGBadge rag={a.overall_rag} recommendation={a.recommendation} />
                  ) : (
                    <StatusPill status={a.status} />
                  )}
                </td>
                <td className="px-4 py-3">
                  <span className="text-xs text-gray-500">{a.review_mode === 'deep_review' ? '🔬 Deep' : '⚡ Standard'}</span>
                </td>
                <td className="px-4 py-3 text-xs text-gray-500">
                  {new Date(a.created_at).toLocaleDateString('en-GB')}
                </td>
                <td className="px-4 py-3 text-right">
                  <Link
                    to={a.status === 'confirming' ? `/assessments/${a.id}/confirm` : `/assessments/${a.id}`}
                    className="text-xs text-blue-400 hover:text-blue-300 font-medium"
                  >
                    View →
                  </Link>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
```

- [ ] **Step 2: Commit**

```bash
git add frontend/src/pages/DashboardPage.tsx
git commit -m "feat: dashboard page with assessment list, filters, search"
```

---

### Task 24: New Assessment, Product Confirmation, and Assessment Detail pages

**Files:**
- Replace: `frontend/src/pages/NewAssessmentPage.tsx`
- Replace: `frontend/src/pages/ProductConfirmationPage.tsx`
- Replace: `frontend/src/pages/AssessmentDetailPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/NewAssessmentPage.tsx`**

```typescript
import { useState, FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { assessmentsApi } from '@/api/assessments'
import type { ReviewMode } from '@/types'

export default function NewAssessmentPage() {
  const navigate = useNavigate()
  const [productName, setProductName] = useState('')
  const [productUrl, setProductUrl] = useState('')
  const [repoUrl, setRepoUrl] = useState('')
  const [reviewMode, setReviewMode] = useState<ReviewMode>('standard')

  const mutation = useMutation({
    mutationFn: () =>
      assessmentsApi.create({
        product_name: productName,
        product_url: productUrl || undefined,
        repo_url: repoUrl || undefined,
        review_mode: reviewMode,
      }),
    onSuccess: (assessment) => {
      if (assessment.status === 'confirming') {
        navigate(`/assessments/${assessment.id}/confirm`)
      } else {
        navigate(`/assessments/${assessment.id}`)
      }
    },
  })

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    mutation.mutate()
  }

  return (
    <Layout>
      <div className="max-w-xl">
        <h1 className="text-xl font-bold text-white mb-1">New Assessment</h1>
        <p className="text-gray-500 text-sm mb-6">Submit a product for security posture analysis.</p>

        <form onSubmit={handleSubmit} className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Product name *</label>
            <input
              value={productName} onChange={(e) => setProductName(e.target.value)}
              required placeholder="e.g. Slack, Notion, my-tool"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Product URL <span className="text-gray-600">(optional)</span></label>
            <input
              value={productUrl} onChange={(e) => setProductUrl(e.target.value)}
              placeholder="https://example.com"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Repository URL <span className="text-gray-600">(optional — enables technical scanning)</span></label>
            <input
              value={repoUrl} onChange={(e) => setRepoUrl(e.target.value)}
              placeholder="https://github.com/org/repo"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500"
            />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-2">Review mode</label>
            <div className="grid grid-cols-2 gap-3">
              {(['standard', 'deep_review'] as ReviewMode[]).map((mode) => (
                <button
                  key={mode} type="button"
                  onClick={() => setReviewMode(mode)}
                  className={`border rounded-lg p-3 text-left transition-colors ${
                    reviewMode === mode
                      ? 'border-blue-500 bg-blue-600/10 text-blue-300'
                      : 'border-gray-700 text-gray-400 hover:border-gray-600'
                  }`}
                >
                  <div className="font-semibold text-sm mb-0.5">
                    {mode === 'standard' ? '⚡ Standard' : '🔬 Deep Review'}
                  </div>
                  <div className="text-xs opacity-70">
                    {mode === 'standard'
                      ? 'Single AI call per module. Fast.'
                      : '5-advisor council per module. Thorough.'}
                  </div>
                </button>
              ))}
            </div>
          </div>

          {mutation.isError && (
            <p className="text-red-400 text-xs">Submission failed. Please try again.</p>
          )}

          <button
            type="submit" disabled={mutation.isPending}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg text-sm disabled:opacity-50"
          >
            {mutation.isPending ? 'Submitting…' : 'Start Assessment'}
          </button>
        </form>
      </div>
    </Layout>
  )
}
```

- [ ] **Step 2: Replace `frontend/src/pages/ProductConfirmationPage.tsx`**

```typescript
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { Layout } from '@/components/Layout'
import { assessmentsApi } from '@/api/assessments'

export default function ProductConfirmationPage() {
  const { id } = useParams<{ id: string }>()
  const navigate = useNavigate()
  const qc = useQueryClient()

  const { data: assessment, isLoading } = useQuery({
    queryKey: ['assessment', id],
    queryFn: () => assessmentsApi.get(id!),
    refetchInterval: 3000,
  })

  const [name, setName] = useState('')
  const [vendor, setVendor] = useState('')
  const [url, setUrl] = useState('')
  const [populated, setPopulated] = useState(false)

  if (!populated && assessment?.product_name) {
    setName(assessment.product_name)
    setPopulated(true)
  }

  const mutation = useMutation({
    mutationFn: () =>
      assessmentsApi.confirmProduct(id!, {
        confirmed_name: name,
        confirmed_vendor: vendor,
        confirmed_url: url,
      }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['assessments'] })
      navigate(`/assessments/${id}`)
    },
  })

  if (isLoading) return <Layout><div className="text-gray-400 p-4">Loading…</div></Layout>

  return (
    <Layout>
      <div className="max-w-lg">
        <h1 className="text-xl font-bold text-white mb-1">Confirm Product Identity</h1>
        <p className="text-gray-500 text-sm mb-6">
          The AI has identified this product. Please confirm or correct the details before the full assessment begins.
        </p>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-4">
          <div>
            <label className="block text-xs text-gray-400 mb-1">Product name</label>
            <input value={name} onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Vendor</label>
            <input value={vendor} onChange={(e) => setVendor(e.target.value)}
              placeholder="e.g. Salesforce, Microsoft, Open Source"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
          </div>
          <div>
            <label className="block text-xs text-gray-400 mb-1">Official URL</label>
            <input value={url} onChange={(e) => setUrl(e.target.value)}
              placeholder="https://..."
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
          </div>

          <div className="flex gap-3 pt-2">
            <button
              onClick={() => mutation.mutate()}
              disabled={mutation.isPending || !name}
              className="flex-1 bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg text-sm disabled:opacity-50"
            >
              {mutation.isPending ? 'Starting analysis…' : '✓ Confirm & Start Analysis'}
            </button>
            <button
              onClick={() => navigate('/')}
              className="px-4 py-2 border border-gray-700 text-gray-400 hover:text-white hover:border-gray-500 rounded-lg text-sm"
            >
              Cancel
            </button>
          </div>
        </div>
      </div>
    </Layout>
  )
}
```

- [ ] **Step 3: Replace `frontend/src/pages/AssessmentDetailPage.tsx`**

```typescript
import { useParams, useNavigate } from 'react-router-dom'
import { useQuery } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { RAGBadge } from '@/components/RAGBadge'
import { FindingCard } from '@/components/FindingCard'
import { assessmentsApi } from '@/api/assessments'
import { useAuth } from '@/auth/AuthContext'

const STATUS_MESSAGES: Record<string, string> = {
  pending: '⏳ Assessment queued…',
  confirming: '🔍 Waiting for product confirmation',
  running: '🔄 Analysis in progress — this may take a few minutes…',
  failed: '❌ Assessment failed. Please try resubmitting.',
}

export default function AssessmentDetailPage() {
  const { id } = useParams<{ id: string }>()
  const { user } = useAuth()
  const canEdit = user?.role === 'analyst' || user?.role === 'admin'

  const { data: assessment, isLoading } = useQuery({
    queryKey: ['assessment', id],
    queryFn: () => assessmentsApi.get(id!),
    refetchInterval: (query) => {
      const status = query.state.data?.status
      return status && ['pending', 'confirming', 'running'].includes(status) ? 4000 : false
    },
  })

  const { data: findings = [] } = useQuery({
    queryKey: ['findings', id],
    queryFn: async () => {
      const a = await assessmentsApi.get(id!)
      return (a as any).findings ?? []
    },
    enabled: assessment?.status === 'complete',
  })

  if (isLoading) return <Layout><div className="text-gray-400 p-4">Loading…</div></Layout>
  if (!assessment) return <Layout><div className="text-red-400 p-4">Assessment not found.</div></Layout>

  const isComplete = assessment.status === 'complete'

  return (
    <Layout>
      <div className="mb-4 flex justify-between items-center">
        <button onClick={() => window.history.back()} className="text-xs text-gray-500 hover:text-white">← Back</button>
        {isComplete && (
          <div className="flex gap-2">
            <a
              href={assessmentsApi.pdfUrl(id!)}
              target="_blank" rel="noopener noreferrer"
              className="text-xs bg-gray-800 hover:bg-gray-700 text-white px-3 py-1.5 rounded-lg border border-gray-700"
            >
              📄 Export PDF
            </a>
          </div>
        )}
      </div>

      {/* Header */}
      <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-5 flex justify-between items-start flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold text-white">{assessment.product_name}</h1>
          <p className="text-gray-500 text-xs mt-0.5">
            {assessment.product_url && <span>{assessment.product_url} · </span>}
            {new Date(assessment.created_at).toLocaleDateString('en-GB')}
            {assessment.review_mode === 'deep_review' && <span className="ml-2 text-purple-400">🔬 Deep Review</span>}
          </p>
        </div>
        {isComplete && assessment.overall_score != null && (
          <div className="text-right">
            <div className={`text-4xl font-black ${
              assessment.overall_rag === 'green' ? 'text-green-400' :
              assessment.overall_rag === 'amber' ? 'text-amber-400' : 'text-red-400'
            }`}>
              {assessment.overall_score.toFixed(1)}<span className="text-lg text-gray-500">/10</span>
            </div>
            <div className="mt-1">
              <RAGBadge rag={assessment.overall_rag!} recommendation={assessment.recommendation!} />
            </div>
          </div>
        )}
      </div>

      {/* In-progress status */}
      {!isComplete && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 text-center text-gray-400">
          {STATUS_MESSAGES[assessment.status] ?? assessment.status}
          {assessment.status === 'confirming' && (
            <div className="mt-3">
              <a href={`/assessments/${id}/confirm`} className="text-xs text-blue-400 hover:text-blue-300">
                → Go to confirmation step
              </a>
            </div>
          )}
        </div>
      )}

      {/* Findings grid */}
      {isComplete && findings.length > 0 && (
        <div className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-4 gap-4">
          {findings.map((f: any) => (
            <FindingCard key={f.id} finding={f} canEdit={canEdit} />
          ))}
        </div>
      )}
    </Layout>
  )
}
```

- [ ] **Step 4: Verify build**

```bash
cd frontend && npm run build
```

Expected: Build succeeds, no TypeScript errors.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/
git commit -m "feat: New Assessment, Product Confirmation, Assessment Detail pages"
```

---

### Task 25: Admin pages

**Files:**
- Replace: `frontend/src/pages/admin/UsersPage.tsx`
- Replace: `frontend/src/pages/admin/AIConfigPage.tsx`

- [ ] **Step 1: Replace `frontend/src/pages/admin/UsersPage.tsx`**

```typescript
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { usersApi } from '@/api/users'
import type { Role, User } from '@/types'

const ROLE_COLOURS: Record<Role, string> = {
  admin: 'text-red-400',
  analyst: 'text-amber-400',
  viewer: 'text-gray-400',
}

export default function UsersPage() {
  const qc = useQueryClient()
  const { data: users = [] } = useQuery({ queryKey: ['users'], queryFn: usersApi.list })

  const [showForm, setShowForm] = useState(false)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [fullName, setFullName] = useState('')
  const [role, setRole] = useState<Role>('viewer')

  const createMutation = useMutation({
    mutationFn: () => usersApi.create({ email, password, full_name: fullName, role }),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['users'] })
      setShowForm(false)
      setEmail(''); setPassword(''); setFullName(''); setRole('viewer')
    },
  })

  const toggleMutation = useMutation({
    mutationFn: ({ id, is_active }: { id: string; is_active: boolean }) =>
      usersApi.update(id, { is_active }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['users'] }),
  })

  return (
    <Layout>
      <div className="flex justify-between items-center mb-6">
        <h1 className="text-xl font-bold text-white">Users</h1>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg"
        >
          + New User
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-900 border border-gray-800 rounded-xl p-5 mb-6">
          <h2 className="font-semibold text-sm text-white mb-4">Create user</h2>
          <div className="grid grid-cols-2 gap-4">
            <div>
              <label className="block text-xs text-gray-400 mb-1">Full name</label>
              <input value={fullName} onChange={(e) => setFullName(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Email</label>
              <input type="email" value={email} onChange={(e) => setEmail(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Password</label>
              <input type="password" value={password} onChange={(e) => setPassword(e.target.value)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
            </div>
            <div>
              <label className="block text-xs text-gray-400 mb-1">Role</label>
              <select value={role} onChange={(e) => setRole(e.target.value as Role)}
                className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500">
                <option value="viewer">Viewer</option>
                <option value="analyst">Analyst</option>
                <option value="admin">Admin</option>
              </select>
            </div>
          </div>
          <div className="flex gap-3 mt-4">
            <button onClick={() => createMutation.mutate()} disabled={createMutation.isPending || !email || !password || !fullName}
              className="bg-blue-600 hover:bg-blue-700 text-white text-sm font-semibold px-4 py-2 rounded-lg disabled:opacity-50">
              Create
            </button>
            <button onClick={() => setShowForm(false)} className="text-sm text-gray-400 hover:text-white px-4 py-2">
              Cancel
            </button>
          </div>
        </div>
      )}

      <div className="bg-gray-900 border border-gray-800 rounded-xl overflow-hidden">
        <table className="w-full text-sm">
          <thead>
            <tr className="border-b border-gray-800 text-xs text-gray-500 uppercase tracking-wider">
              <th className="px-4 py-3 text-left">Name</th>
              <th className="px-4 py-3 text-left">Email</th>
              <th className="px-4 py-3 text-left">Role</th>
              <th className="px-4 py-3 text-left">Status</th>
              <th className="px-4 py-3" />
            </tr>
          </thead>
          <tbody>
            {users.map((u: User) => (
              <tr key={u.id} className="border-t border-gray-800">
                <td className="px-4 py-3 text-white">{u.full_name}</td>
                <td className="px-4 py-3 text-gray-400">{u.email}</td>
                <td className={`px-4 py-3 text-xs font-semibold uppercase ${ROLE_COLOURS[u.role]}`}>{u.role}</td>
                <td className="px-4 py-3">
                  <span className={`text-xs ${u.is_active ? 'text-green-400' : 'text-gray-600'}`}>
                    {u.is_active ? 'Active' : 'Inactive'}
                  </span>
                </td>
                <td className="px-4 py-3 text-right">
                  <button
                    onClick={() => toggleMutation.mutate({ id: u.id, is_active: !u.is_active })}
                    className="text-xs text-gray-500 hover:text-white"
                  >
                    {u.is_active ? 'Deactivate' : 'Activate'}
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Layout>
  )
}
```

- [ ] **Step 2: Replace `frontend/src/pages/admin/AIConfigPage.tsx`**

```typescript
import { useState } from 'react'
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query'
import { Layout } from '@/components/Layout'
import { aiConfigApi } from '@/api/aiConfig'
import type { AIProvider } from '@/types'

const PROVIDER_LABELS: Record<AIProvider, string> = {
  openwebui: 'Open WebUI (local)',
  ollama: 'Ollama (local)',
  gemini: 'Gemini API (cloud)',
}

export default function AIConfigPage() {
  const qc = useQueryClient()
  const { data: config, isLoading } = useQuery({ queryKey: ['ai-config'], queryFn: aiConfigApi.get })

  const [provider, setProvider] = useState<AIProvider>('openwebui')
  const [baseUrl, setBaseUrl] = useState('')
  const [apiKey, setApiKey] = useState('')
  const [modelName, setModelName] = useState('')
  const [populated, setPopulated] = useState(false)

  if (!populated && config) {
    setProvider(config.provider)
    setBaseUrl(config.base_url)
    setModelName(config.model_name)
    setPopulated(true)
  }

  const mutation = useMutation({
    mutationFn: () => aiConfigApi.update({
      provider, base_url: baseUrl,
      ...(apiKey ? { api_key: apiKey } : {}),
      model_name: modelName,
    }),
    onSuccess: () => qc.invalidateQueries({ queryKey: ['ai-config'] }),
  })

  if (isLoading) return <Layout><div className="text-gray-400 p-4">Loading…</div></Layout>

  return (
    <Layout>
      <div className="max-w-lg">
        <h1 className="text-xl font-bold text-white mb-1">AI Provider Config</h1>
        <p className="text-gray-500 text-sm mb-6">Configure the AI backend used for assessments.</p>

        <div className="bg-gray-900 border border-gray-800 rounded-xl p-6 space-y-5">
          <div>
            <label className="block text-xs text-gray-400 mb-2">Provider</label>
            <div className="space-y-2">
              {(['openwebui', 'ollama', 'gemini'] as AIProvider[]).map((p) => (
                <label key={p} className={`flex items-center gap-3 p-3 rounded-lg border cursor-pointer transition-colors ${
                  provider === p ? 'border-blue-500 bg-blue-600/10' : 'border-gray-700 hover:border-gray-600'
                }`}>
                  <input type="radio" value={p} checked={provider === p} onChange={() => setProvider(p)} className="accent-blue-500" />
                  <span className="text-sm text-white">{PROVIDER_LABELS[p]}</span>
                </label>
              ))}
            </div>
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Base URL</label>
            <input value={baseUrl} onChange={(e) => setBaseUrl(e.target.value)}
              placeholder="http://localhost:3000"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">API Key <span className="text-gray-600">(leave blank to keep existing)</span></label>
            <input type="password" value={apiKey} onChange={(e) => setApiKey(e.target.value)}
              placeholder="••••••••"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
          </div>

          <div>
            <label className="block text-xs text-gray-400 mb-1">Model name</label>
            <input value={modelName} onChange={(e) => setModelName(e.target.value)}
              placeholder="llama3, gemma2, gemini-1.5-flash…"
              className="w-full bg-gray-800 border border-gray-700 rounded-lg px-3 py-2 text-sm text-white focus:outline-none focus:border-blue-500" />
          </div>

          {mutation.isSuccess && (
            <p className="text-green-400 text-xs">✓ Configuration saved.</p>
          )}

          <button
            onClick={() => mutation.mutate()} disabled={mutation.isPending}
            className="w-full bg-blue-600 hover:bg-blue-700 text-white font-semibold py-2 rounded-lg text-sm disabled:opacity-50"
          >
            {mutation.isPending ? 'Saving…' : 'Save Configuration'}
          </button>
        </div>
      </div>
    </Layout>
  )
}
```

- [ ] **Step 3: Final build verification**

```bash
cd frontend && npm run build
```

Expected: Build succeeds, no TypeScript errors.

- [ ] **Step 4: Full Docker Compose smoke test**

```bash
# From project root:
docker compose up --build -d
```

Wait ~30 seconds, then:

```bash
# Check all containers are healthy
docker compose ps

# API health
curl -s http://localhost:8000/docs | grep -c "SecurityChecker" || echo "API up"

# Frontend
curl -s http://localhost:3000 | grep -c "SecurityChecker" || echo "Frontend up"
```

- [ ] **Step 5: Commit**

```bash
git add frontend/src/pages/admin/
git commit -m "feat: admin Users and AI Config pages"
```

- [ ] **Step 6: Final commit — Plan 3 complete**

```bash
git add .
git commit -m "feat: Plan 3 complete — full React SPA with all screens"
```

---

**Plan 3 complete.** The full application now has:
- React 18 SPA with Vite, TypeScript, Tailwind CSS
- Login with JWT stored in localStorage
- Protected routes with role-based redirects
- Dashboard with RAG colour coding, filters, and search
- New Assessment form with Standard / Deep Review mode selection
- Product Confirmation step for name-only submissions
- Assessment Detail with live status polling, 8 module finding cards, inline analyst notes
- Admin Users management (create, deactivate, role change)
- Admin AI Config (provider, URL, API key, model name)
- PDF export via direct link to backend endpoint
- Nginx serving SPA + proxying `/api/` to the FastAPI backend

**All three plans complete. The full SecurityChecker application is ready for use.**
