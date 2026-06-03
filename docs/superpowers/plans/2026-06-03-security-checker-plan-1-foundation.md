# SecurityChecker — Plan 1: Foundation

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Scaffold the full project structure, all database models, JWT auth, RBAC, and core CRUD API endpoints — producing a running, tested FastAPI backend accessible via Docker Compose.

**Architecture:** FastAPI (async) with SQLAlchemy 2.0 mapped models and Alembic migrations. PostgreSQL 16 via asyncpg. JWT auth with bcrypt passwords. Role enforcement via FastAPI dependencies. All actions written to audit_log.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 (async), Alembic, asyncpg, pydantic-settings, python-jose, passlib[bcrypt], pytest, pytest-asyncio, httpx.

**Prerequisite plans:** None — this is the starting point.
**Next plans:** Plan 2 (Analysis Engine), Plan 3 (Frontend).

---

## File Map

```
SecurityChecker/
├── docker-compose.yml
├── .env.example
├── .gitignore
├── backend/
│   ├── Dockerfile
│   ├── requirements.txt
│   ├── alembic.ini
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/         # generated migration files
│   └── app/
│       ├── main.py            # FastAPI app factory + router registration
│       ├── config.py          # Settings via pydantic-settings
│       ├── database.py        # Async engine, session dependency
│       ├── models/
│       │   ├── __init__.py
│       │   ├── user.py        # User, Role enum
│       │   ├── assessment.py  # Assessment + all enums (InputType, Status, RAG, etc.)
│       │   ├── finding.py     # AssessmentFinding, Category enum
│       │   ├── product_confirmation.py
│       │   ├── ai_config.py   # AIProviderConfig, Provider enum
│       │   └── audit_log.py   # AuditLog
│       ├── schemas/
│       │   ├── auth.py        # LoginRequest, TokenResponse
│       │   ├── user.py        # UserCreate, UserUpdate, UserOut
│       │   ├── assessment.py  # AssessmentCreate, AssessmentOut, AssessmentDetail
│       │   ├── finding.py     # FindingOut, FindingUpdate
│       │   └── ai_config.py   # AIConfigOut, AIConfigUpdate
│       ├── core/
│       │   ├── security.py    # hash_password, verify_password, create_token, decode_token
│       │   ├── rbac.py        # require_role() dependency factory
│       │   └── audit.py       # log_action() async helper
│       └── api/
│           ├── deps.py        # get_db(), get_current_user()
│           ├── auth.py        # POST /auth/login
│           ├── assessments.py # GET/POST /assessments, GET/PUT /assessments/{id}/findings/{cat}
│           ├── users.py       # GET/POST/PUT /users (Admin only)
│           └── ai_config.py   # GET/PUT /ai-config (Admin only)
tests/
├── conftest.py
├── test_auth.py
├── test_assessments.py
├── test_users.py
└── test_ai_config.py
```

---

### Task 1: Docker Compose scaffold and project structure

**Files:**
- Create: `docker-compose.yml`
- Create: `.env.example`
- Create: `.gitignore`
- Create: `backend/Dockerfile`
- Create: `backend/requirements.txt`

- [ ] **Step 1: Create `.gitignore`**

```
.env
__pycache__/
*.pyc
.pytest_cache/
*.egg-info/
dist/
node_modules/
.superpowers/
```

- [ ] **Step 2: Create `backend/requirements.txt`**

```
fastapi==0.115.0
uvicorn[standard]==0.30.6
sqlalchemy[asyncio]==2.0.35
asyncpg==0.29.0
alembic==1.13.3
pydantic-settings==2.5.2
pydantic[email]==2.9.2
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.12
httpx==0.27.2
celery[redis]==5.4.0
redis==5.1.0
cryptography==43.0.1
weasyprint==62.3
jinja2==3.1.4
pytest==8.3.3
pytest-asyncio==0.24.0
pytest-cov==5.0.0
```

- [ ] **Step 3: Create `backend/Dockerfile`**

```dockerfile
FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    libpango-1.0-0 libpangoft2-1.0-0 libcairo2 libgdk-pixbuf2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

- [ ] **Step 4: Create `.env.example`**

```
POSTGRES_USER=securitychecker
POSTGRES_PASSWORD=changeme
POSTGRES_DB=securitychecker
DATABASE_URL=postgresql+asyncpg://securitychecker:changeme@postgres:5432/securitychecker
REDIS_URL=redis://redis:6379/0
SECRET_KEY=change-this-to-a-random-secret-key-min-32-chars
ENCRYPTION_KEY=change-this-to-a-fernet-key-base64-encoded
OPENWEBUI_BASE_URL=http://localhost:3000
```

- [ ] **Step 5: Create `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: ${POSTGRES_USER}
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
      POSTGRES_DB: ${POSTGRES_DB}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U ${POSTGRES_USER}"]
      interval: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 5

  api:
    build: ./backend
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
    volumes:
      - ./backend:/app
    ports:
      - "8000:8000"
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  worker:
    build: ./backend
    command: celery -A app.worker.celery_app worker --loglevel=info
    volumes:
      - ./backend:/app
    env_file: .env
    depends_on:
      postgres:
        condition: service_healthy
      redis:
        condition: service_healthy

  frontend:
    build: ./frontend
    ports:
      - "3000:80"
    depends_on:
      - api

volumes:
  postgres_data:
```

- [ ] **Step 6: Create directory structure**

```bash
mkdir -p backend/app/{models,schemas,core,api,worker/modules,pdf/templates}
mkdir -p backend/alembic/versions
mkdir -p tests
touch backend/app/__init__.py
touch backend/app/models/__init__.py
touch backend/app/schemas/__init__.py
touch backend/app/core/__init__.py
touch backend/app/api/__init__.py
touch backend/app/worker/__init__.py
touch backend/app/worker/modules/__init__.py
touch backend/app/pdf/__init__.py
touch tests/__init__.py
```

- [ ] **Step 7: Commit**

```bash
git add .
git commit -m "feat: project scaffold, Docker Compose, requirements"
```

---

### Task 2: Settings and database setup

**Files:**
- Create: `backend/app/config.py`
- Create: `backend/app/database.py`

- [ ] **Step 1: Write failing test for settings load**

Create `tests/test_config.py`:

```python
def test_settings_load():
    from app.config import settings
    assert settings.database_url.startswith("postgresql")
    assert len(settings.secret_key) >= 32
```

- [ ] **Step 2: Run test to verify it fails**

```bash
cd backend && DATABASE_URL=postgresql+asyncpg://u:p@localhost/db \
  SECRET_KEY=test-secret-key-at-least-32-chars \
  ENCRYPTION_KEY=dGVzdA== \
  python -m pytest ../tests/test_config.py -v
```

Expected: `ModuleNotFoundError` or `ImportError`

- [ ] **Step 3: Create `backend/app/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str
    redis_url: str = "redis://localhost:6379/0"
    secret_key: str
    encryption_key: str
    openwebui_base_url: str = "http://localhost:3000"
    algorithm: str = "HS256"
    access_token_expire_hours: int = 8

settings = Settings()
```

- [ ] **Step 4: Create `backend/app/database.py`**

```python
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)

class Base(DeclarativeBase):
    pass

async def get_db() -> AsyncSession:
    async with AsyncSessionLocal() as session:
        yield session
```

- [ ] **Step 5: Run test to verify it passes**

```bash
cd backend && DATABASE_URL=postgresql+asyncpg://u:p@localhost/db \
  SECRET_KEY=test-secret-key-at-least-32-chars \
  ENCRYPTION_KEY=dGVzdA== \
  python -m pytest ../tests/test_config.py -v
```

Expected: PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/config.py backend/app/database.py tests/test_config.py
git commit -m "feat: settings and async database setup"
```

---

### Task 3: Database models

**Files:**
- Create: `backend/app/models/user.py`
- Create: `backend/app/models/assessment.py`
- Create: `backend/app/models/finding.py`
- Create: `backend/app/models/product_confirmation.py`
- Create: `backend/app/models/ai_config.py`
- Create: `backend/app/models/audit_log.py`
- Modify: `backend/app/models/__init__.py`

- [ ] **Step 1: Create `backend/app/models/user.py`**

```python
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Boolean, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum
from app.database import Base

class Role(str, enum.Enum):
    ADMIN = "admin"
    ANALYST = "analyst"
    VIEWER = "viewer"

class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    role: Mapped[Role] = mapped_column(SAEnum(Role, name="role_enum"), nullable=False, default=Role.VIEWER)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

- [ ] **Step 2: Create `backend/app/models/assessment.py`**

```python
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum
from app.database import Base

class InputType(str, enum.Enum):
    NAME = "name"
    URL = "url"
    REPO = "repo"

class AssessmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"

class RAGStatus(str, enum.Enum):
    RED = "red"
    AMBER = "amber"
    GREEN = "green"

class Recommendation(str, enum.Enum):
    APPROVE = "approve"
    CONDITIONAL = "conditional"
    REJECT = "reject"

class ReviewMode(str, enum.Enum):
    STANDARD = "standard"
    DEEP_REVIEW = "deep_review"

class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    product_url: Mapped[str | None] = mapped_column(String, nullable=True)
    repo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    input_type: Mapped[InputType] = mapped_column(SAEnum(InputType, name="input_type_enum"), nullable=False)
    status: Mapped[AssessmentStatus] = mapped_column(
        SAEnum(AssessmentStatus, name="assessment_status_enum"), default=AssessmentStatus.PENDING
    )
    review_mode: Mapped[ReviewMode] = mapped_column(
        SAEnum(ReviewMode, name="review_mode_enum"), default=ReviewMode.STANDARD
    )
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_rag: Mapped[RAGStatus | None] = mapped_column(SAEnum(RAGStatus, name="rag_status_enum"), nullable=True)
    recommendation: Mapped[Recommendation | None] = mapped_column(
        SAEnum(Recommendation, name="recommendation_enum"), nullable=True
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(server_default=func.now(), onupdate=func.now())

    findings: Mapped[list["AssessmentFinding"]] = relationship(back_populates="assessment", lazy="selectin")
    product_confirmation: Mapped["ProductConfirmation | None"] = relationship(
        back_populates="assessment", uselist=False, lazy="selectin"
    )
```

- [ ] **Step 3: Create `backend/app/models/finding.py`**

```python
import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Float, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Enum as SAEnum
from app.database import Base
from app.models.assessment import RAGStatus

class Category(str, enum.Enum):
    VENDOR_TRUST = "vendor_trust"
    CVE = "cve"
    MAINTENANCE = "maintenance"
    DEPENDENCY = "dependency"
    ENCRYPTION = "encryption"
    LOGGING = "logging"
    DATA_EXFILTRATION = "data_exfiltration"
    THIRD_PARTY = "third_party"

class AssessmentFinding(Base):
    __tablename__ = "assessment_findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    category: Mapped[Category] = mapped_column(SAEnum(Category, name="category_enum"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rag: Mapped[RAGStatus] = mapped_column(SAEnum(RAGStatus), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(nullable=True)

    assessment: Mapped["Assessment"] = relationship(back_populates="findings")
```

- [ ] **Step 4: Create `backend/app/models/product_confirmation.py`**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class ProductConfirmation(Base):
    __tablename__ = "product_confirmations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    ai_suggested_name: Mapped[str] = mapped_column(String, nullable=False)
    ai_suggested_vendor: Mapped[str] = mapped_column(String, nullable=False)
    ai_suggested_url: Mapped[str] = mapped_column(String, nullable=False)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    assessment: Mapped["Assessment"] = relationship(back_populates="product_confirmation")
```

- [ ] **Step 5: Create `backend/app/models/ai_config.py`**

```python
import uuid
import enum
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum
from app.database import Base

class AIProvider(str, enum.Enum):
    OPENWEBUI = "openwebui"
    OLLAMA = "ollama"
    GEMINI = "gemini"

class AIProviderConfig(Base):
    __tablename__ = "ai_provider_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[AIProvider] = mapped_column(SAEnum(AIProvider, name="ai_provider_enum"), nullable=False)
    base_url: Mapped[str] = mapped_column(String, nullable=False)
    api_key: Mapped[str] = mapped_column(String, nullable=False, default="")
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
```

- [ ] **Step 6: Create `backend/app/models/audit_log.py`**

```python
import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID, JSONB
from app.database import Base

class AuditLog(Base):
    __tablename__ = "audit_log"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    action: Mapped[str] = mapped_column(String, nullable=False)
    resource_type: Mapped[str] = mapped_column(String, nullable=False)
    resource_id: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), nullable=True)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
```

- [ ] **Step 7: Update `backend/app/models/__init__.py`**

```python
from app.models.user import User, Role
from app.models.assessment import Assessment, InputType, AssessmentStatus, RAGStatus, Recommendation, ReviewMode
from app.models.finding import AssessmentFinding, Category
from app.models.product_confirmation import ProductConfirmation
from app.models.ai_config import AIProviderConfig, AIProvider
from app.models.audit_log import AuditLog

__all__ = [
    "User", "Role",
    "Assessment", "InputType", "AssessmentStatus", "RAGStatus", "Recommendation", "ReviewMode",
    "AssessmentFinding", "Category",
    "ProductConfirmation",
    "AIProviderConfig", "AIProvider",
    "AuditLog",
]
```

- [ ] **Step 8: Write model import test**

Create `tests/test_models.py`:

```python
def test_all_models_importable():
    from app.models import (
        User, Role, Assessment, InputType, AssessmentStatus,
        RAGStatus, Recommendation, ReviewMode, AssessmentFinding,
        Category, ProductConfirmation, AIProviderConfig, AIProvider, AuditLog
    )
    assert Role.ADMIN == "admin"
    assert AssessmentStatus.PENDING == "pending"
    assert Category.VENDOR_TRUST == "vendor_trust"
    assert AIProvider.OPENWEBUI == "openwebui"
```

- [ ] **Step 9: Run test to verify it passes**

```bash
cd backend && python -m pytest ../tests/test_models.py -v
```

Expected: PASS

- [ ] **Step 10: Commit**

```bash
git add backend/app/models/ tests/test_models.py
git commit -m "feat: all database models"
```

---

### Task 4: Alembic migrations

**Files:**
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`

- [ ] **Step 1: Initialise Alembic**

```bash
cd backend && alembic init alembic
```

- [ ] **Step 2: Replace `backend/alembic/env.py`**

```python
import asyncio
from logging.config import fileConfig
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import async_engine_from_config
from alembic import context
from app.config import settings
from app.database import Base
import app.models  # ensure all models are registered

config = context.config
config.set_main_option("sqlalchemy.url", settings.database_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()

def do_run_migrations(connection):
    context.configure(connection=connection, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()

def run_migrations_online() -> None:
    asyncio.run(run_async_migrations())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```

- [ ] **Step 3: Generate initial migration**

```bash
cd backend && alembic revision --autogenerate -m "initial schema"
```

Expected: Creates a file in `alembic/versions/` with all 6 table creates.

- [ ] **Step 4: Run migration against running PostgreSQL**

Start only the postgres container:

```bash
docker compose up -d postgres
```

Then run:

```bash
cd backend && alembic upgrade head
```

Expected: `Running upgrade  -> <rev>, initial schema`

- [ ] **Step 5: Verify tables exist**

```bash
docker compose exec postgres psql -U securitychecker -d securitychecker -c "\dt"
```

Expected: Lists `users`, `assessments`, `assessment_findings`, `product_confirmations`, `ai_provider_config`, `audit_log`.

- [ ] **Step 6: Commit**

```bash
git add backend/alembic.ini backend/alembic/
git commit -m "feat: Alembic migrations, initial schema"
```

---

### Task 5: Security utilities (JWT + bcrypt)

**Files:**
- Create: `backend/app/core/security.py`
- Test: `tests/test_security.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_security.py`:

```python
import pytest
from datetime import timedelta

def test_hash_and_verify_password():
    from app.core.security import hash_password, verify_password
    hashed = hash_password("mysecret")
    assert hashed != "mysecret"
    assert verify_password("mysecret", hashed)
    assert not verify_password("wrong", hashed)

def test_create_and_decode_token():
    from app.core.security import create_access_token, decode_access_token
    import uuid
    user_id = uuid.uuid4()
    token = create_access_token(str(user_id), "analyst")
    payload = decode_access_token(token)
    assert payload["sub"] == str(user_id)
    assert payload["role"] == "analyst"

def test_expired_token_raises():
    from app.core.security import create_access_token, decode_access_token
    from jose import JWTError
    import uuid
    token = create_access_token(str(uuid.uuid4()), "viewer", expires_delta=timedelta(seconds=-1))
    with pytest.raises(JWTError):
        decode_access_token(token)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest ../tests/test_security.py -v
```

Expected: `ImportError` — module not found.

- [ ] **Step 3: Create `backend/app/core/security.py`**

```python
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from passlib.context import CryptContext
from app.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain: str, hashed: str) -> bool:
    return pwd_context.verify(plain, hashed)

def create_access_token(user_id: str, role: str, expires_delta: timedelta | None = None) -> str:
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(hours=settings.access_token_expire_hours)
    )
    payload = {"sub": user_id, "role": role, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)

def decode_access_token(token: str) -> dict:
    return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
```

- [ ] **Step 4: Run tests to verify they pass**

```bash
cd backend && python -m pytest ../tests/test_security.py -v
```

Expected: 3 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/core/security.py tests/test_security.py
git commit -m "feat: JWT and bcrypt security utilities"
```

---

### Task 6: FastAPI app factory, schemas, and auth endpoint

**Files:**
- Create: `backend/app/schemas/auth.py`
- Create: `backend/app/schemas/user.py`
- Create: `backend/app/api/deps.py`
- Create: `backend/app/api/auth.py`
- Create: `backend/app/core/audit.py`
- Create: `backend/app/main.py`
- Test: `tests/conftest.py`
- Test: `tests/test_auth.py`

- [ ] **Step 1: Create `backend/app/schemas/auth.py`**

```python
from pydantic import BaseModel, EmailStr

class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
```

- [ ] **Step 2: Create `backend/app/schemas/user.py`**

```python
import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.user import Role

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.VIEWER

class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    is_active: bool | None = None

class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
```

- [ ] **Step 3: Create `backend/app/core/audit.py`**

```python
import uuid
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.audit_log import AuditLog

async def log_action(
    db: AsyncSession,
    user_id: uuid.UUID,
    action: str,
    resource_type: str,
    resource_id: uuid.UUID | None = None,
    detail: dict | None = None,
) -> None:
    entry = AuditLog(
        user_id=user_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        detail=detail or {},
    )
    db.add(entry)
    await db.flush()
```

- [ ] **Step 4: Create `backend/app/api/deps.py`**

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User

bearer = HTTPBearer()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    try:
        payload = decode_access_token(credentials.credentials)
        user_id = payload.get("sub")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == user_id, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
```

- [ ] **Step 5: Create `backend/app/core/rbac.py`**

```python
from fastapi import Depends, HTTPException, status
from app.models.user import User, Role
from app.api.deps import get_current_user

ROLE_ORDER = {Role.VIEWER: 0, Role.ANALYST: 1, Role.ADMIN: 2}

def require_role(minimum_role: Role):
    async def dependency(current_user: User = Depends(get_current_user)) -> User:
        if ROLE_ORDER[current_user.role] < ROLE_ORDER[minimum_role]:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Insufficient permissions")
        return current_user
    return dependency
```

- [ ] **Step 6: Create `backend/app/api/auth.py`**

```python
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.schemas.auth import LoginRequest, TokenResponse
from app.core.security import verify_password, create_access_token
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])

@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.email == body.email, User.is_active == True))
    user = result.scalar_one_or_none()
    if not user or not verify_password(body.password, user.hashed_password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")
    token = create_access_token(str(user.id), user.role.value)
    return TokenResponse(access_token=token)
```

- [ ] **Step 7: Create `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth

app = FastAPI(title="SecurityChecker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
```

- [ ] **Step 8: Create `tests/conftest.py`**

```python
import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database import Base, get_db
from app.models.user import User, Role
from app.core.security import hash_password

TEST_DB_URL = "postgresql+asyncpg://securitychecker:changeme@localhost:5432/securitychecker_test"

test_engine = create_async_engine(TEST_DB_URL)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest_asyncio.fixture(scope="session")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture
async def db(setup_db):
    async with TestSession() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture
async def client(db):
    async def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

async def _make_user(db, email, role, password="password123"):
    user = User(email=email, hashed_password=hash_password(password), full_name="Test User", role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def admin_user(db):
    return await _make_user(db, "admin@test.com", Role.ADMIN)

@pytest_asyncio.fixture
async def analyst_user(db):
    return await _make_user(db, "analyst@test.com", Role.ANALYST)

@pytest_asyncio.fixture
async def viewer_user(db):
    return await _make_user(db, "viewer@test.com", Role.VIEWER)

async def login(client, email, password="password123"):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]
```

Note: the test database `securitychecker_test` must exist. Create it:

```bash
docker compose exec postgres psql -U securitychecker -c "CREATE DATABASE securitychecker_test;"
```

- [ ] **Step 9: Write failing auth tests**

Create `tests/test_auth.py`:

```python
import pytest

@pytest.mark.asyncio
async def test_login_success(client, analyst_user):
    r = await client.post("/api/v1/auth/login", json={"email": "analyst@test.com", "password": "password123"})
    assert r.status_code == 200
    data = r.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"

@pytest.mark.asyncio
async def test_login_wrong_password(client, analyst_user):
    r = await client.post("/api/v1/auth/login", json={"email": "analyst@test.com", "password": "wrong"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_login_unknown_email(client):
    r = await client.post("/api/v1/auth/login", json={"email": "nobody@test.com", "password": "password123"})
    assert r.status_code == 401

@pytest.mark.asyncio
async def test_protected_route_no_token(client):
    r = await client.get("/api/v1/assessments")
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_protected_route_invalid_token(client):
    r = await client.get("/api/v1/assessments", headers={"Authorization": "Bearer notavalidtoken"})
    assert r.status_code == 401
```

- [ ] **Step 10: Run tests (last two will 404 until assessments router exists — that's fine)**

```bash
cd backend && python -m pytest ../tests/test_auth.py::test_login_success ../tests/test_auth.py::test_login_wrong_password ../tests/test_auth.py::test_login_unknown_email -v
```

Expected: 3 PASS

- [ ] **Step 11: Commit**

```bash
git add backend/app/ tests/conftest.py tests/test_auth.py
git commit -m "feat: FastAPI app, auth endpoint, JWT deps, RBAC, audit helper"
```

---

### Task 7: Assessment schemas and CRUD API

**Files:**
- Create: `backend/app/schemas/assessment.py`
- Create: `backend/app/schemas/finding.py`
- Create: `backend/app/api/assessments.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_assessments.py`

- [ ] **Step 1: Create `backend/app/schemas/assessment.py`**

```python
import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.assessment import InputType, AssessmentStatus, RAGStatus, Recommendation, ReviewMode

class AssessmentCreate(BaseModel):
    product_name: str
    product_url: str | None = None
    repo_url: str | None = None
    review_mode: ReviewMode = ReviewMode.STANDARD

class ProductConfirmRequest(BaseModel):
    confirmed_name: str
    confirmed_vendor: str
    confirmed_url: str

class AssessmentOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    product_name: str
    product_url: str | None
    repo_url: str | None
    input_type: InputType
    status: AssessmentStatus
    review_mode: ReviewMode
    overall_score: float | None
    overall_rag: RAGStatus | None
    recommendation: Recommendation | None
    submitted_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
```

- [ ] **Step 2: Create `backend/app/schemas/finding.py`**

```python
import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.finding import Category
from app.models.assessment import RAGStatus

class FindingOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    assessment_id: uuid.UUID
    category: Category
    score: float
    rag: RAGStatus
    summary: str
    detail: dict
    analyst_notes: str | None
    edited_by: uuid.UUID | None
    edited_at: datetime | None

class FindingUpdate(BaseModel):
    analyst_notes: str | None = None
    score: float | None = None
```

- [ ] **Step 3: Create `backend/app/api/assessments.py`**

```python
import uuid
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Role
from app.models.assessment import Assessment, InputType, AssessmentStatus
from app.models.finding import AssessmentFinding, Category
from app.models.product_confirmation import ProductConfirmation
from app.schemas.assessment import AssessmentCreate, AssessmentOut, ProductConfirmRequest
from app.schemas.finding import FindingOut, FindingUpdate
from app.api.deps import get_current_user
from app.core.rbac import require_role
from app.core.audit import log_action
from app.worker.celery_app import celery_app

router = APIRouter(prefix="/assessments", tags=["assessments"])

def _derive_input_type(body: AssessmentCreate) -> InputType:
    if body.repo_url:
        return InputType.REPO
    if body.product_url:
        return InputType.URL
    return InputType.NAME

@router.get("", response_model=list[AssessmentOut])
async def list_assessments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.VIEWER)),
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
):
    q = select(Assessment).order_by(Assessment.created_at.desc()).offset(skip).limit(limit)
    if status_filter:
        q = q.where(Assessment.status == status_filter)
    result = await db.execute(q)
    return result.scalars().all()

@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    body: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ANALYST)),
):
    input_type = _derive_input_type(body)
    assessment = Assessment(
        product_name=body.product_name,
        product_url=body.product_url,
        repo_url=body.repo_url,
        input_type=input_type,
        review_mode=body.review_mode,
        submitted_by=current_user.id,
        status=AssessmentStatus.PENDING,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    await log_action(db, current_user.id, "submit_assessment", "assessment", assessment.id)
    await db.commit()

    # Enqueue Celery job (implemented in Plan 2)
    celery_app.send_task("app.worker.tasks.run_assessment", args=[str(assessment.id)])

    return assessment

@router.get("/{assessment_id}", response_model=AssessmentOut)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.VIEWER)),
):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment

@router.post("/{assessment_id}/confirm-product", response_model=AssessmentOut)
async def confirm_product(
    assessment_id: uuid.UUID,
    body: ProductConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ANALYST)),
):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status != AssessmentStatus.CONFIRMING:
        raise HTTPException(status_code=400, detail="Assessment is not awaiting confirmation")

    conf_result = await db.execute(
        select(ProductConfirmation).where(ProductConfirmation.assessment_id == assessment_id)
    )
    confirmation = conf_result.scalar_one_or_none()
    if confirmation:
        confirmation.confirmed_by = current_user.id
        confirmation.confirmed_at = datetime.now(timezone.utc)

    assessment.product_name = body.confirmed_name
    assessment.product_url = body.confirmed_url or assessment.product_url
    assessment.status = AssessmentStatus.RUNNING
    await db.commit()
    await db.refresh(assessment)

    celery_app.send_task("app.worker.tasks.run_analysis", args=[str(assessment_id)])
    return assessment

@router.put("/{assessment_id}/findings/{category}", response_model=FindingOut)
async def update_finding(
    assessment_id: uuid.UUID,
    category: Category,
    body: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ANALYST)),
):
    result = await db.execute(
        select(AssessmentFinding).where(
            AssessmentFinding.assessment_id == assessment_id,
            AssessmentFinding.category == category,
        )
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    if body.analyst_notes is not None:
        finding.analyst_notes = body.analyst_notes
    if body.score is not None:
        finding.score = body.score
    finding.edited_by = current_user.id
    finding.edited_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(finding)
    await log_action(db, current_user.id, "edit_finding", "finding", finding.id,
                     {"category": category.value})
    await db.commit()
    return finding
```

- [ ] **Step 4: Create a stub `backend/app/worker/celery_app.py`** (full impl in Plan 2)

```python
from celery import Celery
from app.config import settings

celery_app = Celery("securitychecker", broker=settings.redis_url, backend=settings.redis_url)
celery_app.conf.task_always_eager = False
```

- [ ] **Step 5: Register the assessments router in `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, assessments

app = FastAPI(title="SecurityChecker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
```

- [ ] **Step 6: Write failing tests**

Create `tests/test_assessments.py`:

```python
import pytest
from tests.conftest import login

@pytest.mark.asyncio
async def test_viewer_cannot_submit(client, viewer_user):
    token = await login(client, "viewer@test.com")
    r = await client.post(
        "/api/v1/assessments",
        json={"product_name": "Slack"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_analyst_can_submit(client, analyst_user):
    token = await login(client, "analyst@test.com")
    r = await client.post(
        "/api/v1/assessments",
        json={"product_name": "Slack", "review_mode": "standard"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    data = r.json()
    assert data["product_name"] == "Slack"
    assert data["input_type"] == "name"
    assert data["status"] == "pending"

@pytest.mark.asyncio
async def test_repo_url_sets_input_type_repo(client, analyst_user):
    token = await login(client, "analyst@test.com")
    r = await client.post(
        "/api/v1/assessments",
        json={"product_name": "MyTool", "repo_url": "https://github.com/org/repo"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["input_type"] == "repo"

@pytest.mark.asyncio
async def test_viewer_can_list(client, viewer_user, analyst_user, db):
    from app.models.assessment import Assessment, InputType, AssessmentStatus, ReviewMode
    a = Assessment(
        product_name="TestApp", input_type=InputType.NAME,
        status=AssessmentStatus.COMPLETE, review_mode=ReviewMode.STANDARD,
        submitted_by=analyst_user.id,
    )
    db.add(a)
    await db.commit()

    token = await login(client, "viewer@test.com")
    r = await client.get("/api/v1/assessments", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert any(item["product_name"] == "TestApp" for item in r.json())

@pytest.mark.asyncio
async def test_unauthenticated_cannot_list(client):
    r = await client.get("/api/v1/assessments")
    assert r.status_code == 403
```

- [ ] **Step 7: Run tests**

```bash
cd backend && python -m pytest ../tests/test_assessments.py -v
```

Expected: 5 PASS (Celery send_task will succeed silently even without broker in tests)

- [ ] **Step 8: Run all auth tests to confirm no regression**

```bash
cd backend && python -m pytest ../tests/test_auth.py ../tests/test_assessments.py -v
```

Expected: All PASS

- [ ] **Step 9: Commit**

```bash
git add backend/app/schemas/ backend/app/api/assessments.py backend/app/api/__init__.py \
        backend/app/worker/celery_app.py backend/app/main.py tests/test_assessments.py
git commit -m "feat: assessments CRUD API with RBAC"
```

---

### Task 8: Users API (Admin)

**Files:**
- Create: `backend/app/api/users.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_users.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_users.py`:

```python
import pytest
from tests.conftest import login

@pytest.mark.asyncio
async def test_analyst_cannot_list_users(client, analyst_user):
    token = await login(client, "analyst@test.com")
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_admin_can_list_users(client, admin_user, viewer_user):
    token = await login(client, "admin@test.com")
    r = await client.get("/api/v1/users", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    emails = [u["email"] for u in r.json()]
    assert "admin@test.com" in emails

@pytest.mark.asyncio
async def test_admin_can_create_user(client, admin_user):
    token = await login(client, "admin@test.com")
    r = await client.post(
        "/api/v1/users",
        json={"email": "newuser@test.com", "password": "pass1234", "full_name": "New User", "role": "viewer"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 201
    assert r.json()["email"] == "newuser@test.com"

@pytest.mark.asyncio
async def test_admin_can_deactivate_user(client, admin_user, viewer_user):
    token = await login(client, "admin@test.com")
    r = await client.put(
        f"/api/v1/users/{viewer_user.id}",
        json={"is_active": False},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["is_active"] is False
```

- [ ] **Step 2: Create `backend/app/api/users.py`**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.core.security import hash_password
from app.core.rbac import require_role
from app.core.audit import log_action

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await log_action(db, current_user.id, "create_user", "user", user.id)
    await db.commit()
    return user

@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    await db.commit()
    await db.refresh(user)
    await log_action(db, current_user.id, "update_user", "user", user_id)
    await db.commit()
    return user
```

- [ ] **Step 3: Register users router in `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, assessments, users

app = FastAPI(title="SecurityChecker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest ../tests/test_users.py -v
```

Expected: 4 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/api/users.py backend/app/main.py tests/test_users.py
git commit -m "feat: users admin API"
```

---

### Task 9: AI Config API (Admin)

**Files:**
- Create: `backend/app/schemas/ai_config.py`
- Create: `backend/app/api/ai_config.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_ai_config.py`

- [ ] **Step 1: Create `backend/app/schemas/ai_config.py`**

```python
import uuid
from pydantic import BaseModel
from app.models.ai_config import AIProvider

class AIConfigOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    provider: AIProvider
    base_url: str
    model_name: str
    is_active: bool

class AIConfigUpdate(BaseModel):
    provider: AIProvider | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    is_active: bool | None = None
```

- [ ] **Step 2: Write failing tests**

Create `tests/test_ai_config.py`:

```python
import pytest
from tests.conftest import login
from app.models.ai_config import AIProviderConfig, AIProvider

@pytest.fixture
async def ai_config(db):
    config = AIProviderConfig(
        provider=AIProvider.OPENWEBUI,
        base_url="http://localhost:3000",
        api_key="",
        model_name="llama3",
        is_active=True,
    )
    db.add(config)
    await db.commit()
    await db.refresh(config)
    return config

@pytest.mark.asyncio
async def test_analyst_cannot_get_ai_config(client, analyst_user, ai_config):
    token = await login(client, "analyst@test.com")
    r = await client.get("/api/v1/ai-config", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403

@pytest.mark.asyncio
async def test_admin_can_get_ai_config(client, admin_user, ai_config):
    token = await login(client, "admin@test.com")
    r = await client.get("/api/v1/ai-config", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 200
    assert r.json()["provider"] == "openwebui"
    assert "api_key" not in r.json()

@pytest.mark.asyncio
async def test_admin_can_update_ai_config(client, admin_user, ai_config):
    token = await login(client, "admin@test.com")
    r = await client.put(
        "/api/v1/ai-config",
        json={"model_name": "gemma2"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 200
    assert r.json()["model_name"] == "gemma2"
```

- [ ] **Step 3: Create `backend/app/api/ai_config.py`**

```python
from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.config import settings
from app.models.user import User, Role
from app.models.ai_config import AIProviderConfig
from app.schemas.ai_config import AIConfigOut, AIConfigUpdate
from app.core.rbac import require_role
from app.core.audit import log_action

router = APIRouter(prefix="/ai-config", tags=["ai-config"])

def _encrypt(value: str) -> str:
    if not value:
        return ""
    f = Fernet(settings.encryption_key.encode())
    return f.encrypt(value.encode()).decode()

@router.get("", response_model=AIConfigOut)
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.is_active == True))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="No active AI provider configured")
    return config

@router.put("", response_model=AIConfigOut)
async def update_ai_config(
    body: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.is_active == True))
    config = result.scalar_one_or_none()
    if not config:
        config = AIProviderConfig(is_active=True)
        db.add(config)

    if body.provider is not None:
        config.provider = body.provider
    if body.base_url is not None:
        config.base_url = body.base_url
    if body.api_key is not None:
        config.api_key = _encrypt(body.api_key)
    if body.model_name is not None:
        config.model_name = body.model_name

    await db.commit()
    await db.refresh(config)
    await log_action(db, current_user.id, "update_ai_config", "ai_config", config.id)
    await db.commit()
    return config
```

- [ ] **Step 4: Register ai_config router in `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, assessments, users, ai_config

app = FastAPI(title="SecurityChecker API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1")
app.include_router(assessments.router, prefix="/api/v1")
app.include_router(users.router, prefix="/api/v1")
app.include_router(ai_config.router, prefix="/api/v1")
```

- [ ] **Step 5: Run all tests**

```bash
cd backend && python -m pytest ../tests/ -v
```

Expected: All PASS

- [ ] **Step 6: Commit**

```bash
git add backend/app/schemas/ai_config.py backend/app/api/ai_config.py backend/app/main.py tests/test_ai_config.py
git commit -m "feat: AI config admin API with encrypted key storage"
```

---

### Task 10: Seed script and end-to-end smoke test

**Files:**
- Create: `backend/scripts/seed.py`

- [ ] **Step 1: Create `backend/scripts/seed.py`**

```python
"""Run with: cd backend && python scripts/seed.py"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.database import Base
from app.models.user import User, Role
from app.models.ai_config import AIProviderConfig, AIProvider
from app.core.security import hash_password

async def seed():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        admin = User(
            email="admin@securitychecker.local",
            hashed_password=hash_password("changeme"),
            full_name="Admin",
            role=Role.ADMIN,
        )
        config = AIProviderConfig(
            provider=AIProvider.OPENWEBUI,
            base_url=settings.openwebui_base_url,
            api_key="",
            model_name="llama3",
            is_active=True,
        )
        db.add(admin)
        db.add(config)
        await db.commit()
        print("Seeded: admin@securitychecker.local / changeme")
        print(f"Seeded: OpenWebUI config → {settings.openwebui_base_url}")

asyncio.run(seed())
```

- [ ] **Step 2: Copy `.env.example` to `.env` and fill in values**

```bash
cp .env.example .env
# Edit .env: set POSTGRES_PASSWORD, SECRET_KEY (random 32+ chars), ENCRYPTION_KEY (Fernet key)
# Generate a Fernet key:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

- [ ] **Step 3: Start all containers and run migrations**

```bash
docker compose up -d postgres redis
cd backend && alembic upgrade head
```

- [ ] **Step 4: Seed the database**

```bash
cd backend && python scripts/seed.py
```

Expected: `Seeded: admin@securitychecker.local / changeme`

- [ ] **Step 5: Start the API and smoke test with curl**

```bash
docker compose up -d api

# Login
curl -s -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"admin@securitychecker.local","password":"changeme"}' | python -m json.tool
```

Expected: JSON with `access_token`.

- [ ] **Step 6: Run the full test suite**

```bash
cd backend && python -m pytest ../tests/ -v --tb=short
```

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/scripts/ .env.example
git commit -m "feat: seed script, Plan 1 complete — foundation API ready"
```

---

**Plan 1 complete.** The running system now has:
- Docker Compose stack (postgres + redis + api + worker skeleton + frontend placeholder)
- All 6 database models with Alembic migrations
- JWT auth with bcrypt
- RBAC (Viewer / Analyst / Admin) enforced via FastAPI dependencies
- Assessments CRUD, Users admin, AI Config admin APIs
- Audit logging on all mutations
- Full test suite

**Continue with:** `2026-06-03-security-checker-plan-2-analysis-engine.md`
