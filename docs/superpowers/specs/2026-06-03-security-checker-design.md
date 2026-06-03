# SecurityChecker — Design Spec

**Date:** 2026-06-03  
**Status:** Approved

---

## Purpose

SecurityChecker is an AI-driven tool for assessing the security posture of software products as part of a formal software approval process. Analysts submit a product name, URL, or repository, and the system produces a scored, RAG-rated report covering eight security categories. Reports are stored historically and can be exported as PDF.

---

## Architecture

### Stack

- **Backend:** Python 3.12, FastAPI, SQLAlchemy (async), Alembic
- **Task queue:** Celery + Redis
- **Database:** PostgreSQL 16
- **Frontend:** React 18 + TypeScript, Vite, served via Nginx
- **PDF generation:** WeasyPrint (Jinja2 HTML template → PDF)
- **Containerisation:** Docker Compose

### Containers

| Container | Purpose |
|-----------|---------|
| `frontend` | React + TypeScript SPA, served by Nginx on port 3000 |
| `api` | FastAPI application, port 8000 |
| `worker` | Celery worker (same Python image, different entrypoint) |
| `redis` | Celery broker and result backend |
| `postgres` | PostgreSQL 16 database |

A single `docker-compose.yml` at project root starts all five containers. An Nginx reverse proxy in the `frontend` container proxies `/api/` to the `api` container so the browser only talks to one origin.

### Assessment Job Flow

1. User submits product name / URL / repo via web UI or API
2. API creates an `Assessment` record (status: `pending`) and enqueues a Celery job
3. If input is a product name only, worker runs a quick product lookup (web search + AI) and returns a suggested product identity (name, vendor, URL)
4. User confirms the identified product via a confirmation step in the UI
5. Worker runs all 8 analysis modules (parallelised where possible)
6. Each module writes its findings to `assessment_findings`
7. Worker computes per-category scores and RAG, derives overall score and recommendation, updates `Assessment` to `complete`
8. User views results in UI or downloads PDF

---

## AI Provider

### Primary: Open WebUI API

The system talks to a locally-running Open WebUI instance via its OpenAI-compatible API. Provider, base URL, API key, and model name are stored in `ai_provider_config` and configurable by Admin users at runtime.

### Supported providers

| Provider | Type |
|----------|------|
| Open WebUI | Local (primary) |
| Ollama | Local (alternative) |
| Gemini API | Cloud (alternative) |

All providers are accessed through a single `AIClient` abstraction in the worker. Switching provider requires only updating `ai_provider_config` — no code changes.

---

## Analysis Modules

Eight modules run per assessment. Each returns a `score` (0.0–10.0), `rag` (red/amber/green), a short `summary`, and a `detail` JSON blob with raw findings. Scores are weighted and averaged to produce the overall score; weights are configurable by Admin.

| # | Module | Data sources |
|---|--------|-------------|
| 1 | **Vendor Trust** | Web search, AI synthesis |
| 2 | **CVE & Vulnerability History** | NVD/NIST API, web search, AI synthesis |
| 3 | **Maintenance & Activity** | GitHub/GitLab API, web search, AI synthesis |
| 4 | **Dependency Risk** | Trivy, pip-audit, npm audit (if repo provided); AI synthesis (if name/URL only) |
| 5 | **Encryption** | Repo scan, docs, web search, AI synthesis |
| 6 | **Logging & Monitoring** | Docs, web search, AI synthesis |
| 7 | **Data Exfiltration Risk** | Repo scan, privacy policy, web search, AI synthesis |
| 8 | **Third-party Integrations** | Repo scan, docs, web search, AI synthesis |

### Input type determines analysis depth

- **Product name only:** Web search + AI synthesis for all modules. No repo scanning.
- **URL provided:** Web search + AI synthesis + any publicly accessible docs/privacy policy.
- **Repo URL provided:** Full technical scanning (Trivy, pip-audit/npm audit) + web search + AI synthesis.

### Scoring thresholds (defaults, configurable)

| Overall score | RAG | Recommendation |
|---------------|-----|----------------|
| 7.5–10 | Green | Approve |
| 5.0–7.4 | Amber | Conditional Approval |
| 0–4.9 | Red | Reject |

---

## Database Schema

### `users`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| email | varchar unique | |
| hashed_password | varchar | bcrypt |
| full_name | varchar | |
| role | enum | admin / analyst / viewer |
| is_active | bool | default true |
| created_at | timestamptz | |

### `assessments`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| product_name | varchar | |
| product_url | varchar | nullable |
| repo_url | varchar | nullable |
| input_type | enum | name / url / repo — repo takes precedence if repo_url is provided |
| status | enum | pending / confirming / running / complete / failed |
| overall_score | float | nullable until complete |
| overall_rag | enum | red / amber / green — nullable until complete |
| recommendation | enum | approve / conditional / reject — nullable until complete |
| submitted_by | uuid FK → users | |
| created_at | timestamptz | |
| updated_at | timestamptz | |

### `product_confirmations`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| assessment_id | uuid FK → assessments | |
| ai_suggested_name | varchar | |
| ai_suggested_vendor | varchar | |
| ai_suggested_url | varchar | |
| confirmed_by | uuid FK → users | nullable until confirmed |
| confirmed_at | timestamptz | nullable until confirmed |

### `assessment_findings`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| assessment_id | uuid FK → assessments | |
| category | enum | vendor_trust / cve / maintenance / dependency / encryption / logging / data_exfiltration / third_party |
| score | float | 0.0–10.0 |
| rag | enum | red / amber / green |
| summary | text | AI-generated short summary |
| detail | jsonb | raw findings |
| analyst_notes | text | editable by Analyst+ |
| edited_by | uuid FK → users | nullable |
| edited_at | timestamptz | nullable |

### `ai_provider_config`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| provider | enum | openwebui / ollama / gemini |
| base_url | varchar | |
| api_key | varchar | encrypted at rest |
| model_name | varchar | |
| is_active | bool | only one active at a time |

### `audit_log`

| Column | Type | Notes |
|--------|------|-------|
| id | uuid PK | |
| user_id | uuid FK → users | |
| action | varchar | e.g. submit_assessment, approve, edit_finding |
| resource_type | varchar | |
| resource_id | uuid | |
| detail | jsonb | before/after or context |
| created_at | timestamptz | |

---

## RBAC

| Action | Viewer | Analyst | Admin |
|--------|--------|---------|-------|
| View assessments and reports | ✓ | ✓ | ✓ |
| Download PDF | ✓ | ✓ | ✓ |
| Submit new assessment | | ✓ | ✓ |
| Confirm product identity | | ✓ | ✓ |
| Edit findings / add analyst notes | | ✓ | ✓ |
| Approve / conditionally approve / reject | | ✓ | ✓ |
| Manage users | | | ✓ |
| Configure AI provider | | | ✓ |
| Configure score weights | | | ✓ |

---

## REST API

All routes prefixed `/api/v1/`. Authentication via JWT bearer token. API key auth also supported for machine-to-machine integration.

| Method | Path | Role required | Notes |
|--------|------|---------------|-------|
| POST | `/auth/login` | — | Returns JWT |
| GET | `/assessments` | Viewer+ | Paginated list with filters |
| POST | `/assessments` | Analyst+ | Submits new assessment |
| GET | `/assessments/{id}` | Viewer+ | Full detail including findings |
| POST | `/assessments/{id}/confirm-product` | Analyst+ | Confirms AI product suggestion |
| PUT | `/assessments/{id}/findings/{category}` | Analyst+ | Edit notes, override score |
| GET | `/assessments/{id}/pdf` | Viewer+ | Download PDF report |
| GET | `/users` | Admin | List users |
| POST | `/users` | Admin | Create user |
| PUT | `/users/{id}` | Admin | Update user / role |
| GET | `/ai-config` | Admin | Get current AI provider config |
| PUT | `/ai-config` | Admin | Update AI provider config |

---

## UI Screens

1. **Login** — email/password form
2. **Dashboard** — paginated assessment list with RAG colour coding, score, recommendation, status, and filters (RAG, status, search)
3. **New Assessment** — form: product name, URL (optional), repo URL (optional)
4. **Product Confirmation** — AI-suggested name, vendor, and URL; Accept / Edit / Try Again
5. **Assessment Detail** — product header with overall score and RAG; 8 module cards each showing score, RAG, summary, and analyst notes field; Export PDF and Mark Approved/Rejected actions
6. **Admin — Users** — user list with create/edit/deactivate
7. **Admin — AI Config** — provider selection, URL, API key, model name

---

## PDF Report

Generated server-side using WeasyPrint from a Jinja2 HTML template. Structure:

- **Page 1:** Cover — product name, vendor, overall score, RAG, recommendation, assessment metadata, executive summary, category score bar chart, analyst notes/conditions
- **Pages 2–9:** One page per module — category name, score, RAG, full findings detail, data sources used
- **Final page:** Methodology note, disclaimer, assessment ID

PDF is stored as a file reference and regenerated on demand (not persisted to disk permanently).

---

## Security Considerations

- Passwords hashed with bcrypt
- API keys in `ai_provider_config` encrypted at rest (Fernet symmetric encryption, key from environment variable)
- JWT tokens expire after 8 hours
- All actions logged to `audit_log`
- Repo cloning (for technical scanning) runs in an isolated temp directory, cleaned up after the job
- No user-supplied input is passed directly to shell commands — all scanning tools invoked via subprocess with explicit argument lists

---

## Docker Compose Environment Variables

```
POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB
REDIS_URL
SECRET_KEY                  # JWT signing key
ENCRYPTION_KEY              # Fernet key for API key encryption
OPENWEBUI_BASE_URL          # Default AI provider URL
```

All secrets passed via `.env` file (not committed). A `.env.example` is provided.
