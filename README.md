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
5. **Executive summary** AI-generated structured overview with posture, strengths, concerns, and next steps
6. **Run history** — last 3 re-runs retained per assessment with date, operator, and scores
7. **PDF export** of the full report including executive summary and module findings
8. **Methodology page** — in-app documentation explaining scoring weights, RAG thresholds, and module logic
9. **Deep Review mode** runs a 5-advisor council (Threat Modeler, Compliance Officer, Risk Analyst, Devil's Advocate, Pragmatist) with anonymous peer review and chairman synthesis per module — produces more rigorous, UK Defence-aligned analysis (JSP 440, JSP 604, Cyber Essentials, NCSC CAF)

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

The seed script generates a **random admin password** on first run and prints it once to stdout. Save it — it will not be shown again.

```bash
# View the generated password from compose logs
docker compose logs api | grep "Seeded:"
```

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
| `CORS_ORIGINS` | Comma-separated allowed origins (default: `http://localhost:3000`) |

### AI provider (in-app)

Navigate to **Admin → AI Config**. Each provider (Ollama, Open WebUI, Gemini) has independent settings — save each separately, then click **Set Active** to switch. Settings for inactive providers are preserved.

| Provider | Base URL example | Notes |
|---|---|---|
| Ollama | `http://host.containers.internal:11434` | Must bind to `0.0.0.0`: `OLLAMA_HOST=0.0.0.0 ollama serve` |
| Open WebUI | `http://your-openwebui-host:3000` | Uses `/api/chat/completions` |
| Gemini | `https://generativelanguage.googleapis.com` | API key encrypted at rest |

> **Podman + suspend/resume**: `host.containers.internal` may stop resolving after laptop suspend. Use the host's LAN IP (e.g. `http://192.168.1.x:11434`) as a workaround, or restart containers after resume.

Use **Test Active Provider** to validate before running assessments.

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

- **Re-run**: run all modules again with a different review mode or updated scope — previous results snapshotted to run history
- **Run history**: last 3 re-runs retained per assessment (date, operator, score, RAG)
- **Single-module re-run**: re-run one specific module via `POST /api/v1/assessments/{id}/modules/{category}/rerun`
- **Delete**: removes assessment and all findings (owner or admin only)
- **Progress tracking**: live module progress and elapsed timer shown during analysis

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
GET    /api/v1/ai-config
PUT    /api/v1/ai-config/{provider}
POST   /api/v1/ai-config/{provider}/activate
POST   /api/v1/ai-config/test
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
- `host.containers.internal` may break after laptop suspend/resume — restart containers or use host LAN IP
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

---

## Licence

Copyright 2026 SimonNyx. Licensed under the [Apache License 2.0](LICENSE).
