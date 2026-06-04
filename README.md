# SecurityChecker

AI-driven security posture assessment tool. Takes a product name, URL, or GitHub repo and produces a structured security report across 8 risk categories, scored and RAG-rated, with optional PDF export.

---

## What it does

1. **Submit** a product (name, URL, or GitHub repo URL)
2. **AI product lookup** resolves vendor/version — auto-confirms high-confidence matches, prompts user confirmation otherwise
3. **Analysis** runs 8 security modules in parallel:
   - Vendor Trust
   - CVE History
   - Maintenance & Activity
   - Dependency Risk (clones repo, runs Trivy + pip-audit if available)
   - Encryption Posture
   - Logging & Monitoring
   - Data Exfiltration Risk
   - Third-Party Integrations
4. **Results** scored 0–10 per module, aggregated to an overall RAG (Red/Amber/Green) and recommendation (Approve / Conditional / Reject)
5. **PDF export** of the full report
6. **Deep Review mode** runs a 5-advisor council (Threat Modeler, Compliance Officer, Risk Analyst, Devil's Advocate, Pragmatist) with anonymous peer review and chairman synthesis per module — produces more rigorous, UK Defence-aligned analysis (JSP 440, JSP 604, Cyber Essentials, NCSC CAF)

---

## Stack

| Layer | Technology |
|---|---|
| API | Python 3.12, FastAPI (async), SQLAlchemy 2.0, asyncpg |
| Queue | Celery + Redis |
| Database | PostgreSQL 16 |
| PDF | WeasyPrint + Jinja2 |
| Frontend | React 18, TypeScript, Vite, Tailwind CSS, TanStack Query v5 |
| AI | Ollama, Open WebUI, or Gemini API (configurable) |
| Container | Docker / Podman Compose |

---

## Prerequisites

- Docker or Podman with Compose plugin
- An AI provider, one of:
  - **Ollama** running locally (`OLLAMA_HOST=0.0.0.0 ollama serve`)
  - **Open WebUI** instance
  - **Gemini API** key

---

## Quick start

```bash
# 1. Clone and configure
cp .env.example .env
# Edit .env — set SECRET_KEY, ENCRYPTION_KEY, and database password

# 2. Generate keys
python3 -c "import secrets; print(secrets.token_hex(32))"          # SECRET_KEY
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"  # ENCRYPTION_KEY

# 3. Start backend services
docker compose up -d

# 4. Start frontend (optional)
docker compose --profile frontend up -d frontend
```

API: http://localhost:8000  
UI: http://localhost:3000  
Default credentials: `admin@securitychecker.local` / `changeme`

---

## Configuration

### Environment variables (`.env`)

| Variable | Description |
|---|---|
| `DATABASE_URL` | PostgreSQL async connection string |
| `REDIS_URL` | Redis connection string |
| `SECRET_KEY` | JWT signing secret (min 32 chars) |
| `ENCRYPTION_KEY` | Fernet key for encrypting AI API keys at rest |
| `POSTGRES_USER` / `PASSWORD` / `DB` | Postgres credentials |

### AI provider (in-app)

Navigate to **Admin → AI Config** and configure:

| Provider | Base URL example | Notes |
|---|---|---|
| Ollama | `http://host.containers.internal:11434` | Must bind to `0.0.0.0` not `127.0.0.1` |
| Open WebUI | `http://your-openwebui-host:3000` | Uses `/api/chat/completions` |
| Gemini | `https://generativelanguage.googleapis.com` | Requires API key |

Use **Test Connection** to validate before running assessments.

---

## Roles

| Role | Permissions |
|---|---|
| `viewer` | Read assessments |
| `analyst` | Create, confirm, re-run, delete assessments; edit findings |
| `admin` | All above + manage users and AI config |

---

## Assessment workflow

```
Submit → PENDING
       → CONFIRMING  (AI looked up product, needs user confirmation if low confidence)
       → RUNNING     (modules executing)
       → COMPLETE / FAILED
```

- **Re-run**: run all modules again with a different review mode
- **Single-module re-run**: re-run one specific module via `POST /api/v1/assessments/{id}/modules/{category}/rerun`
- **Delete**: removes assessment and all findings

---

## API

Interactive docs at http://localhost:8000/docs

Key endpoints:

```
POST   /api/v1/auth/login
GET    /api/v1/assessments
POST   /api/v1/assessments
GET    /api/v1/assessments/{id}
POST   /api/v1/assessments/{id}/confirm
POST   /api/v1/assessments/{id}/rerun
POST   /api/v1/assessments/{id}/modules/{category}/rerun
DELETE /api/v1/assessments/{id}
GET    /api/v1/assessments/{id}/pdf
PUT    /api/v1/assessments/{id}/findings/{category}
GET    /api/v1/admin/ai-config
PUT    /api/v1/admin/ai-config
POST   /api/v1/admin/ai-config/test
GET    /api/v1/admin/users
```

---

## Development

```bash
# Run backend with live reload (already default in compose)
docker compose up api worker

# Rebuild frontend after code changes
docker compose --profile frontend build frontend
docker compose --profile frontend up -d frontend

# Run backend tests
cd backend && pytest

# Alembic migrations
docker compose exec api alembic revision --autogenerate -m "description"
docker compose exec api alembic upgrade head
```

### Podman notes

- Use `host.containers.internal` instead of `host-gateway` for host networking
- Ollama must bind to `0.0.0.0`: `OLLAMA_HOST=0.0.0.0 ollama serve`
- nginx DNS resolver auto-detected from `/etc/resolv.conf` at container startup

---

## Project structure

```
.
├── backend/
│   ├── app/
│   │   ├── api/          # FastAPI route handlers
│   │   ├── core/         # Security, RBAC, audit logging
│   │   ├── models/       # SQLAlchemy ORM models
│   │   ├── schemas/      # Pydantic schemas
│   │   ├── pdf/          # WeasyPrint PDF generation
│   │   └── worker/
│   │       ├── modules/  # 8 analysis modules
│   │       ├── council.py         # Deep review advisor system
│   │       ├── tasks.py           # Celery task definitions
│   │       └── ai_client.py       # AI provider abstraction
│   ├── alembic/          # Database migrations
│   └── scripts/          # Seed script
├── frontend/
│   └── src/
│       ├── pages/        # Route-level components
│       ├── components/   # Shared UI components
│       ├── api/          # Axios API clients
│       └── context/      # Auth context
└── docker-compose.yml
```
