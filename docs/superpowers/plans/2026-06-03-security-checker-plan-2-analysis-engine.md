# SecurityChecker — Plan 2: Analysis Engine

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Implement the Celery worker, AI client abstraction, all 8 analysis modules (Standard and Deep Review council modes), score aggregation, and PDF export — producing fully functional security assessments.

**Architecture:** Celery task receives an assessment ID, runs product lookup if needed, dispatches 8 analysis modules (asyncio-parallelised within the task), aggregates scores, writes findings to PostgreSQL, and triggers PDF generation on demand. Deep Review mode runs each module's raw data through a 5-advisor council with peer review and chairman synthesis.

**Tech Stack:** Celery, Redis, httpx (async), asyncpg, Trivy (subprocess), pip-audit (subprocess), npm audit (subprocess), WeasyPrint, Jinja2, NVD/NIST API, GitHub API.

**Prerequisite plan:** Plan 1 (Foundation) must be complete and all tests passing.

---

## File Map

```
backend/app/worker/
├── celery_app.py      # Celery instance (replace stub from Plan 1)
├── tasks.py           # run_assessment() + run_analysis() Celery tasks
├── ai_client.py       # AIClient abstraction (OpenWebUI / Ollama / Gemini)
├── product_lookup.py  # resolve_product() — web search + AI identity suggestion
├── scoring.py         # score_to_rag(), aggregate_scores(), derive_recommendation()
├── council.py         # run_council(raw_data, category) for Deep Review mode
└── modules/
    ├── base.py              # BaseModule abstract class
    ├── vendor_trust.py
    ├── cve.py
    ├── maintenance.py
    ├── dependency.py
    ├── encryption.py
    ├── logging_module.py
    ├── data_exfiltration.py
    └── third_party.py

backend/app/pdf/
├── generator.py           # generate_pdf(assessment_data) → bytes
└── templates/report.html.j2

backend/app/api/pdf.py     # GET /assessments/{id}/pdf

tests/
├── test_scoring.py
├── test_council.py
└── test_modules.py
```

---

### Task 11: Celery app and async DB helper for worker

**Files:**
- Replace: `backend/app/worker/celery_app.py`
- Create: `backend/app/worker/db.py`

- [ ] **Step 1: Replace `backend/app/worker/celery_app.py`**

```python
from celery import Celery
from app.config import settings

celery_app = Celery(
    "securitychecker",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=["app.worker.tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
)
```

- [ ] **Step 2: Create `backend/app/worker/db.py`**

Worker tasks run synchronously in Celery but need async DB access. This helper runs async DB operations in a dedicated event loop.

```python
import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

_engine = create_async_engine(settings.database_url)
_Session = async_sessionmaker(_engine, expire_on_commit=False)

@asynccontextmanager
async def worker_db():
    async with _Session() as session:
        yield session
        await session.commit()

def run_async(coro):
    """Run an async coroutine from sync Celery task code."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
    except RuntimeError:
        pass
    return asyncio.run(coro)
```

- [ ] **Step 3: Commit**

```bash
git add backend/app/worker/celery_app.py backend/app/worker/db.py
git commit -m "feat: Celery app config and worker DB helper"
```

---

### Task 12: AI client abstraction

**Files:**
- Create: `backend/app/worker/ai_client.py`
- Test: `tests/test_ai_client.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_ai_client.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_ai_client_complete_returns_string():
    from app.worker.ai_client import AIClient
    config = {
        "provider": "openwebui",
        "base_url": "http://localhost:3000",
        "api_key": "",
        "model_name": "llama3",
    }
    client = AIClient(config)
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "choices": [{"message": {"content": "This is the AI response."}}]
    }
    mock_response.raise_for_status = AsyncMock()
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await client.complete("Say hello")
    assert result == "This is the AI response."

@pytest.mark.asyncio
async def test_ai_client_gemini_provider():
    from app.worker.ai_client import AIClient
    config = {
        "provider": "gemini",
        "base_url": "https://generativelanguage.googleapis.com",
        "api_key": "fake-key",
        "model_name": "gemini-1.5-flash",
    }
    client = AIClient(config)
    mock_response = AsyncMock()
    mock_response.json.return_value = {
        "candidates": [{"content": {"parts": [{"text": "Gemini says hello."}]}}]
    }
    mock_response.raise_for_status = AsyncMock()
    with patch("httpx.AsyncClient.post", return_value=mock_response):
        result = await client.complete("Say hello")
    assert result == "Gemini says hello."
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest ../tests/test_ai_client.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `backend/app/worker/ai_client.py`**

```python
import httpx
from app.models.ai_config import AIProvider

class AIClient:
    def __init__(self, config: dict):
        self.provider = config["provider"]
        self.base_url = config["base_url"].rstrip("/")
        self.api_key = config.get("api_key", "")
        self.model = config["model_name"]

    async def complete(self, prompt: str, system: str = "") -> str:
        if self.provider in (AIProvider.OPENWEBUI, AIProvider.OLLAMA):
            return await self._openai_complete(prompt, system)
        elif self.provider == AIProvider.GEMINI:
            return await self._gemini_complete(prompt, system)
        raise ValueError(f"Unknown provider: {self.provider}")

    async def _openai_complete(self, prompt: str, system: str) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        async with httpx.AsyncClient(timeout=120) as http:
            resp = await http.post(
                f"{self.base_url}/api/chat/completions",
                headers=headers,
                json={"model": self.model, "messages": messages},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def _gemini_complete(self, prompt: str, system: str) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent?key={self.api_key}"
        async with httpx.AsyncClient(timeout=120) as http:
            resp = await http.post(
                url,
                json={"contents": [{"parts": [{"text": full_prompt}]}]},
            )
            resp.raise_for_status()
            return resp.json()["candidates"][0]["content"]["parts"][0]["text"]


async def get_ai_client_from_db() -> AIClient:
    """Load the active AI config from DB and return a configured client."""
    from sqlalchemy import select
    from app.worker.db import worker_db
    from app.models.ai_config import AIProviderConfig
    from cryptography.fernet import Fernet
    from app.config import settings

    async with worker_db() as db:
        result = await db.execute(
            select(AIProviderConfig).where(AIProviderConfig.is_active == True)
        )
        config = result.scalar_one_or_none()
        if not config:
            raise RuntimeError("No active AI provider configured")

        api_key = ""
        if config.api_key:
            f = Fernet(settings.encryption_key.encode())
            api_key = f.decrypt(config.api_key.encode()).decode()

        return AIClient({
            "provider": config.provider,
            "base_url": config.base_url,
            "api_key": api_key,
            "model_name": config.model_name,
        })
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest ../tests/test_ai_client.py -v
```

Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/worker/ai_client.py tests/test_ai_client.py
git commit -m "feat: AI client abstraction (OpenWebUI, Ollama, Gemini)"
```

---

### Task 13: Scoring utilities

**Files:**
- Create: `backend/app/worker/scoring.py`
- Test: `tests/test_scoring.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_scoring.py`:

```python
import pytest

def test_score_to_rag_green():
    from app.worker.scoring import score_to_rag
    from app.models.assessment import RAGStatus
    assert score_to_rag(8.0) == RAGStatus.GREEN
    assert score_to_rag(7.5) == RAGStatus.GREEN
    assert score_to_rag(10.0) == RAGStatus.GREEN

def test_score_to_rag_amber():
    from app.worker.scoring import score_to_rag
    from app.models.assessment import RAGStatus
    assert score_to_rag(7.4) == RAGStatus.AMBER
    assert score_to_rag(5.0) == RAGStatus.AMBER

def test_score_to_rag_red():
    from app.worker.scoring import score_to_rag
    from app.models.assessment import RAGStatus
    assert score_to_rag(4.9) == RAGStatus.RED
    assert score_to_rag(0.0) == RAGStatus.RED

def test_derive_recommendation():
    from app.worker.scoring import derive_recommendation
    from app.models.assessment import RAGStatus, Recommendation
    assert derive_recommendation(RAGStatus.GREEN) == Recommendation.APPROVE
    assert derive_recommendation(RAGStatus.AMBER) == Recommendation.CONDITIONAL
    assert derive_recommendation(RAGStatus.RED) == Recommendation.REJECT

def test_aggregate_scores_equal_weights():
    from app.worker.scoring import aggregate_scores
    scores = {"vendor_trust": 8.0, "cve": 6.0, "maintenance": 7.0,
              "dependency": 5.0, "encryption": 9.0, "logging": 6.0,
              "data_exfiltration": 7.0, "third_party": 8.0}
    weights = {k: 1.0 for k in scores}
    result = aggregate_scores(scores, weights)
    assert abs(result - 7.0) < 0.01

def test_aggregate_scores_weighted():
    from app.worker.scoring import aggregate_scores
    scores = {"vendor_trust": 10.0, "cve": 0.0}
    weights = {"vendor_trust": 1.0, "cve": 3.0}
    result = aggregate_scores(scores, weights)
    assert abs(result - 2.5) < 0.01
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
cd backend && python -m pytest ../tests/test_scoring.py -v
```

Expected: `ImportError`

- [ ] **Step 3: Create `backend/app/worker/scoring.py`**

```python
from app.models.assessment import RAGStatus, Recommendation
from app.models.finding import Category

DEFAULT_WEIGHTS = {
    Category.VENDOR_TRUST: 1.0,
    Category.CVE: 2.0,
    Category.MAINTENANCE: 1.5,
    Category.DEPENDENCY: 1.5,
    Category.ENCRYPTION: 1.5,
    Category.LOGGING: 1.0,
    Category.DATA_EXFILTRATION: 1.5,
    Category.THIRD_PARTY: 1.0,
}

def score_to_rag(score: float) -> RAGStatus:
    if score >= 7.5:
        return RAGStatus.GREEN
    if score >= 5.0:
        return RAGStatus.AMBER
    return RAGStatus.RED

def derive_recommendation(rag: RAGStatus) -> Recommendation:
    return {
        RAGStatus.GREEN: Recommendation.APPROVE,
        RAGStatus.AMBER: Recommendation.CONDITIONAL,
        RAGStatus.RED: Recommendation.REJECT,
    }[rag]

def aggregate_scores(scores: dict[str, float], weights: dict[str, float]) -> float:
    total_weight = sum(weights[k] for k in scores if k in weights)
    if total_weight == 0:
        return 0.0
    weighted_sum = sum(scores[k] * weights.get(k, 1.0) for k in scores)
    return round(weighted_sum / total_weight, 2)
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest ../tests/test_scoring.py -v
```

Expected: 6 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/worker/scoring.py tests/test_scoring.py
git commit -m "feat: scoring utilities (RAG, recommendation, weighted aggregation)"
```

---

### Task 14: Analysis module base class and product lookup

**Files:**
- Create: `backend/app/worker/modules/base.py`
- Create: `backend/app/worker/product_lookup.py`
- Test: `tests/test_modules.py` (partial)

- [ ] **Step 1: Create `backend/app/worker/modules/base.py`**

```python
from abc import ABC, abstractmethod
from dataclasses import dataclass
from app.models.assessment import Assessment, RAGStatus
from app.worker.ai_client import AIClient

@dataclass
class ModuleResult:
    score: float       # 0.0–10.0
    rag: RAGStatus
    summary: str       # 1-3 sentence human-readable summary
    detail: dict       # raw structured findings for audit/PDF

class BaseModule(ABC):
    category: str      # must match Category enum value

    def __init__(self, assessment: Assessment, ai_client: AIClient):
        self.assessment = assessment
        self.ai = ai_client

    @abstractmethod
    async def run(self) -> ModuleResult:
        """Gather data and return a ModuleResult."""

    async def _ask_ai(self, prompt: str, system: str = "") -> str:
        return await self.ai.complete(prompt, system)
```

- [ ] **Step 2: Create `backend/app/worker/product_lookup.py`**

```python
import json
from app.worker.ai_client import AIClient

LOOKUP_SYSTEM = """You are a software product identification assistant.
Given a product name, identify the correct software product.
Respond with JSON only, no markdown, in this exact format:
{"name": "...", "vendor": "...", "url": "...", "confidence": "high|medium|low", "description": "..."}"""

async def resolve_product(product_name: str, ai_client: AIClient) -> dict:
    """Ask the AI to identify a product by name. Returns suggestion dict."""
    prompt = f"""Identify this software product: "{product_name}"

Return the official product name, the vendor/company that makes it, 
the official website URL, your confidence level, and a one-sentence description.
If this is an open-source project, the vendor is the maintainer organisation.
Respond with JSON only."""

    response = await ai_client.complete(prompt, system=LOOKUP_SYSTEM)

    try:
        # Strip any accidental markdown fences
        clean = response.strip().strip("```json").strip("```").strip()
        return json.loads(clean)
    except json.JSONDecodeError:
        return {
            "name": product_name,
            "vendor": "Unknown",
            "url": "",
            "confidence": "low",
            "description": response[:200],
        }
```

- [ ] **Step 3: Write failing product lookup test**

Add to `tests/test_modules.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch

@pytest.mark.asyncio
async def test_resolve_product_parses_json():
    from app.worker.product_lookup import resolve_product
    from app.worker.ai_client import AIClient

    mock_config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(mock_config)
    client.complete = AsyncMock(return_value='{"name":"Slack","vendor":"Salesforce","url":"https://slack.com","confidence":"high","description":"Team messaging"}')

    result = await resolve_product("Slack", client)
    assert result["name"] == "Slack"
    assert result["vendor"] == "Salesforce"
    assert result["confidence"] == "high"

@pytest.mark.asyncio
async def test_resolve_product_handles_bad_json():
    from app.worker.product_lookup import resolve_product
    from app.worker.ai_client import AIClient

    mock_config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(mock_config)
    client.complete = AsyncMock(return_value="I cannot identify that product.")

    result = await resolve_product("??gibberish??", client)
    assert result["name"] == "??gibberish??"
    assert result["confidence"] == "low"
```

- [ ] **Step 4: Run tests**

```bash
cd backend && python -m pytest ../tests/test_modules.py -v
```

Expected: 2 PASS

- [ ] **Step 5: Commit**

```bash
git add backend/app/worker/modules/base.py backend/app/worker/product_lookup.py tests/test_modules.py
git commit -m "feat: module base class and product lookup"
```

---

### Task 15: All 8 analysis modules (Standard mode)

**Files:**
- Create: `backend/app/worker/modules/vendor_trust.py`
- Create: `backend/app/worker/modules/cve.py`
- Create: `backend/app/worker/modules/maintenance.py`
- Create: `backend/app/worker/modules/dependency.py`
- Create: `backend/app/worker/modules/encryption.py`
- Create: `backend/app/worker/modules/logging_module.py`
- Create: `backend/app/worker/modules/data_exfiltration.py`
- Create: `backend/app/worker/modules/third_party.py`

Each module follows the same pattern: gather context from data sources, build a prompt, ask the AI to return JSON with `score`, `summary`, and `findings`. The AI prompt includes the scoring rubric.

The JSON schema every module's AI call must return:
```json
{
  "score": 7.5,
  "summary": "One to three sentence summary of findings.",
  "findings": { ...module-specific structured data... }
}
```

- [ ] **Step 1: Create `backend/app/worker/modules/vendor_trust.py`**

```python
import json
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing vendor trust for a software approval process.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"company": "...", "founded": "...", "size": "...", "type": "commercial|open_source|foundation", "security_programme": "...", "known_incidents": [...], "certifications": [...]}}
Score rubric: 9-10=major trusted vendor, active security programme, no incidents; 7-8=established vendor, minor incidents resolved; 5-6=smaller vendor, limited transparency; 3-4=unknown/very small, no security programme; 0-2=known bad actor or abandoned."""

class VendorTrustModule(BaseModule):
    category = "vendor_trust"

    async def run(self) -> ModuleResult:
        prompt = f"""Assess vendor trust for: {self.assessment.product_name}
Vendor website: {self.assessment.product_url or 'unknown'}

Research: company identity, size, funding/ownership, security programme, certifications (ISO27001, SOC2), known security incidents, open source vs commercial, community health if OSS.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"raw": data.get("findings", {}), "ai_response": response},
        )
```

- [ ] **Step 2: Create `backend/app/worker/modules/cve.py`**

```python
import json
import httpx
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing CVE history for software approval.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"total_cves": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "recent_cves": [...], "avg_patch_days": null, "unpatched_critical": 0}}
Score rubric: 9-10=no CVEs or only low severity resolved quickly; 7-8=few medium CVEs, patched within 30 days; 5-6=several high CVEs, patched within 90 days; 3-4=critical CVEs or slow patching; 0-2=unpatched critical CVEs or history of ignoring vulnerabilities."""

async def _fetch_nvd(product_name: str) -> list[dict]:
    """Query NVD API for recent CVEs. Returns list of CVE summaries."""
    try:
        async with httpx.AsyncClient(timeout=20) as http:
            resp = await http.get(
                "https://services.nvd.nist.gov/rest/json/cves/2.0",
                params={"keywordSearch": product_name, "resultsPerPage": 20},
            )
            resp.raise_for_status()
            items = resp.json().get("vulnerabilities", [])
            return [
                {
                    "id": v["cve"]["id"],
                    "severity": v["cve"].get("metrics", {}).get("cvssMetricV31", [{}])[0].get("cvssData", {}).get("baseSeverity", "UNKNOWN"),
                    "description": v["cve"]["descriptions"][0]["value"][:200],
                    "published": v["cve"]["published"][:10],
                }
                for v in items
            ]
    except Exception:
        return []

class CVEModule(BaseModule):
    category = "cve"

    async def run(self) -> ModuleResult:
        nvd_data = await _fetch_nvd(self.assessment.product_name)

        prompt = f"""Assess CVE and vulnerability history for: {self.assessment.product_name}

NVD data (last 20 results):
{json.dumps(nvd_data, indent=2)}

Additional context: research recent security advisories, patch cadence, responsible disclosure programme.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"nvd_raw": nvd_data, "findings": data.get("findings", {}), "ai_response": response},
        )
```

- [ ] **Step 3: Create `backend/app/worker/modules/maintenance.py`**

```python
import json
import httpx
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing software maintenance and activity.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"last_release": "...", "release_cadence": "...", "latest_version": "...", "is_eol": false, "commit_frequency": "...", "issue_response_time": "...", "security_advisories_published": true}}
Score rubric: 9-10=active releases, regular patches, security advisories published; 7-8=regular releases, responsive to issues; 5-6=infrequent releases but not abandoned; 3-4=last release >1 year ago; 0-2=abandoned, EOL, no maintenance."""

async def _fetch_github_repo(repo_url: str) -> dict:
    if not repo_url or "github.com" not in repo_url:
        return {}
    try:
        parts = repo_url.rstrip("/").split("github.com/")[-1].split("/")
        owner, repo = parts[0], parts[1]
        async with httpx.AsyncClient(timeout=15, headers={"Accept": "application/vnd.github+json"}) as http:
            r = await http.get(f"https://api.github.com/repos/{owner}/{repo}")
            r.raise_for_status()
            d = r.json()
            return {
                "pushed_at": d.get("pushed_at", "")[:10],
                "open_issues": d.get("open_issues_count", 0),
                "stargazers": d.get("stargazers_count", 0),
                "archived": d.get("archived", False),
            }
    except Exception:
        return {}

class MaintenanceModule(BaseModule):
    category = "maintenance"

    async def run(self) -> ModuleResult:
        github_data = await _fetch_github_repo(self.assessment.repo_url or "")

        prompt = f"""Assess maintenance and activity for: {self.assessment.product_name}
Website: {self.assessment.product_url or 'unknown'}
Repo: {self.assessment.repo_url or 'unknown'}
GitHub data: {json.dumps(github_data)}

Research: last release date, release frequency, changelog, EOL status, security advisory publication, issue response time.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"github": github_data, "findings": data.get("findings", {}), "ai_response": response},
        )
```

- [ ] **Step 4: Create `backend/app/worker/modules/dependency.py`**

```python
import json
import subprocess
import tempfile
import os
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing software dependency risk.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"vulnerable_deps": 0, "critical_vulns": 0, "high_vulns": 0, "outdated_deps": 0, "total_deps": 0, "scanner_used": "...", "notable_issues": [...]}}
Score rubric: 9-10=no vulnerable deps; 7-8=low severity only, all outdated non-critical; 5-6=some medium vulns; 3-4=high vulns present; 0-2=critical vulns in dependencies or known compromised packages."""

def _run_trivy(repo_path: str) -> dict:
    try:
        result = subprocess.run(
            ["trivy", "fs", "--format", "json", "--quiet", repo_path],
            capture_output=True, text=True, timeout=120
        )
        return json.loads(result.stdout) if result.stdout else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return {}

def _run_pip_audit(repo_path: str) -> dict:
    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json", "-r", os.path.join(repo_path, "requirements.txt")],
            capture_output=True, text=True, timeout=60
        )
        return json.loads(result.stdout) if result.stdout else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return {}

def _clone_repo(repo_url: str, target_dir: str) -> bool:
    result = subprocess.run(
        ["git", "clone", "--depth", "1", repo_url, target_dir],
        capture_output=True, timeout=120
    )
    return result.returncode == 0

class DependencyModule(BaseModule):
    category = "dependency"

    async def run(self) -> ModuleResult:
        scan_data = {}
        scanner_used = "ai_synthesis"

        if self.assessment.repo_url:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_dir = os.path.join(tmpdir, "repo")
                if _clone_repo(self.assessment.repo_url, repo_dir):
                    trivy = _run_trivy(repo_dir)
                    pip = _run_pip_audit(repo_dir)
                    scan_data = {"trivy": trivy, "pip_audit": pip}
                    scanner_used = "trivy+pip_audit"

        prompt = f"""Assess dependency risk for: {self.assessment.product_name}
Repo: {self.assessment.repo_url or 'not provided'}
Scanner results: {json.dumps(scan_data) if scan_data else 'No repo scan available — use AI synthesis from public information.'}

Identify vulnerable, outdated, or risky dependencies. Note any known supply-chain incidents.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        if "scanner_used" not in data.get("findings", {}):
            data.setdefault("findings", {})["scanner_used"] = scanner_used

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"scan": scan_data, "findings": data.get("findings", {}), "ai_response": response},
        )
```

- [ ] **Step 5: Create `backend/app/worker/modules/encryption.py`**

```python
import json
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing encryption practices.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"tls_version": "...", "at_rest_encryption": "...", "key_management": "...", "weak_protocols": [...], "certifications": [...], "fips_compliant": false}}
Score rubric: 9-10=TLS1.3, AES-256 at rest, HSM or cloud KMS, FIPS compliant; 7-8=TLS1.2+, AES-256, documented key rotation; 5-6=TLS1.2, encryption claimed but not detailed; 3-4=TLS1.0/1.1 still supported or weak ciphers; 0-2=no encryption or plaintext storage documented."""

class EncryptionModule(BaseModule):
    category = "encryption"

    async def run(self) -> ModuleResult:
        prompt = f"""Assess encryption in transit and at rest for: {self.assessment.product_name}
Website: {self.assessment.product_url or 'unknown'}
Repo: {self.assessment.repo_url or 'unknown'}

Research: TLS version support, at-rest encryption algorithm, key management approach, 
weak protocol support (SSLv3, TLS1.0, TLS1.1), FIPS compliance, encryption certifications.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"findings": data.get("findings", {}), "ai_response": response},
        )
```

- [ ] **Step 6: Create `backend/app/worker/modules/logging_module.py`**

```python
import json
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing logging and monitoring capabilities.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"audit_log_available": false, "audit_log_plan": "...", "siem_integrations": [...], "log_format": "structured|unstructured|mixed", "log_retention": "...", "compliance_logging": [...], "real_time_alerts": false}}
Score rubric: 9-10=full audit log, SIEM integration, structured logs, compliance logging (SOC2/ISO27001); 7-8=audit log available, some integrations; 5-6=basic logging, no SIEM; 3-4=limited logging, enterprise plan only; 0-2=no audit logging capability."""

class LoggingModule(BaseModule):
    category = "logging"

    async def run(self) -> ModuleResult:
        prompt = f"""Assess logging and monitoring capabilities for: {self.assessment.product_name}
Website: {self.assessment.product_url or 'unknown'}

Research: audit log availability and plan tier, SIEM integration support (Splunk, Sentinel, etc.),
log format (structured JSON vs plain text), retention policies, compliance logging for SOC2/ISO27001/Cyber Essentials.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"findings": data.get("findings", {}), "ai_response": response},
        )
```

- [ ] **Step 7: Create `backend/app/worker/modules/data_exfiltration.py`**

```python
import json
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing data exfiltration risk.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"telemetry_present": true, "telemetry_opt_out": false, "data_residency": "...", "gdpr_compliant": false, "data_shared_with": [...], "privacy_policy_url": "...", "known_incidents": [...], "dpa_available": false}}
Score rubric: 9-10=no telemetry or fully opt-out, data stays on-premise or clear residency, GDPR+DPA; 7-8=minimal telemetry, opt-out available, GDPR compliant; 5-6=telemetry present, GDPR claimed; 3-4=extensive telemetry, no opt-out, vague privacy policy; 0-2=known data sharing incidents or no privacy policy."""

class DataExfiltrationModule(BaseModule):
    category = "data_exfiltration"

    async def run(self) -> ModuleResult:
        prompt = f"""Assess data exfiltration risk for: {self.assessment.product_name}
Website: {self.assessment.product_url or 'unknown'}
Repo: {self.assessment.repo_url or 'unknown'}

Research: telemetry and analytics (can it be disabled?), privacy policy, data residency and sovereignty,
GDPR compliance, UK GDPR, DPA availability, data shared with third parties, any known data breach or exfiltration incidents.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"findings": data.get("findings", {}), "ai_response": response},
        )
```

- [ ] **Step 8: Create `backend/app/worker/modules/third_party.py`**

```python
import json
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing third-party integration risk.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"cloud_providers": [...], "identity_providers": [...], "payment_processors": [...], "analytics_services": [...], "other_integrations": [...], "risk_notes": "..."}}
Score rubric: 9-10=only well-known, well-governed providers (AWS/Azure/GCP, Google/MS SSO); 7-8=reputable providers, some smaller services; 5-6=mix of well-known and less-known providers; 3-4=high-risk or unknown third-party services; 0-2=known compromised or sanctioned third-party providers."""

class ThirdPartyModule(BaseModule):
    category = "third_party"

    async def run(self) -> ModuleResult:
        prompt = f"""Assess third-party integration risk for: {self.assessment.product_name}
Website: {self.assessment.product_url or 'unknown'}
Repo: {self.assessment.repo_url or 'unknown'}

Research: cloud infrastructure providers, SSO/identity providers, payment processors, 
analytics/tracking services, CDN providers, any other external service dependencies.
Assess the security posture of each third party.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"findings": data.get("findings", {}), "ai_response": response},
        )
```

- [ ] **Step 9: Write module tests (mocked AI)**

Add to `tests/test_modules.py`:

```python
@pytest.mark.asyncio
async def test_vendor_trust_module_returns_result():
    from app.worker.modules.vendor_trust import VendorTrustModule
    from app.worker.ai_client import AIClient
    from app.models.assessment import Assessment, InputType, ReviewMode, AssessmentStatus

    assessment = Assessment(
        product_name="Slack",
        product_url="https://slack.com",
        input_type=InputType.URL,
        review_mode=ReviewMode.STANDARD,
        status=AssessmentStatus.RUNNING,
        submitted_by=__import__("uuid").uuid4(),
    )
    config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(config)
    client.complete = AsyncMock(return_value='{"score": 8.5, "summary": "Trusted vendor.", "findings": {"company": "Salesforce"}}')

    module = VendorTrustModule(assessment, client)
    result = await module.run()

    assert result.score == 8.5
    assert result.summary == "Trusted vendor."
    from app.models.assessment import RAGStatus
    assert result.rag == RAGStatus.GREEN

@pytest.mark.asyncio
async def test_module_handles_invalid_ai_json():
    from app.worker.modules.vendor_trust import VendorTrustModule
    from app.worker.ai_client import AIClient
    from app.models.assessment import Assessment, InputType, ReviewMode, AssessmentStatus

    assessment = Assessment(
        product_name="Unknown",
        input_type=InputType.NAME,
        review_mode=ReviewMode.STANDARD,
        status=AssessmentStatus.RUNNING,
        submitted_by=__import__("uuid").uuid4(),
    )
    config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(config)
    client.complete = AsyncMock(return_value="This is not JSON at all.")

    module = VendorTrustModule(assessment, client)
    result = await module.run()
    assert result.score == 5.0  # default fallback
```

- [ ] **Step 10: Run all module tests**

```bash
cd backend && python -m pytest ../tests/test_modules.py -v
```

Expected: All PASS

- [ ] **Step 11: Commit**

```bash
git add backend/app/worker/modules/ tests/test_modules.py
git commit -m "feat: all 8 analysis modules (Standard mode)"
```

---

### Task 16: Council mode (Deep Review)

**Files:**
- Create: `backend/app/worker/council.py`
- Test: `tests/test_council.py`

- [ ] **Step 1: Write failing tests**

Create `tests/test_council.py`:

```python
import pytest
from unittest.mock import AsyncMock

@pytest.mark.asyncio
async def test_council_returns_module_result():
    from app.worker.council import run_council
    from app.worker.ai_client import AIClient
    from app.models.finding import Category

    config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(config)

    advisor_response = '{"score": 7.0, "summary": "Moderate risk.", "findings": {}}'
    review_response = "Response A is strongest. Response B misses X. All miss Y."
    chairman_response = '{"score": 6.5, "summary": "Balanced view.", "findings": {"council": true}}'

    call_count = 0
    async def mock_complete(prompt, system=""):
        nonlocal call_count
        call_count += 1
        if call_count <= 5:
            return advisor_response
        elif call_count <= 10:
            return review_response
        else:
            return chairman_response

    client.complete = mock_complete

    raw_data = {"product": "TestApp", "nvd_data": []}
    result = await run_council(raw_data, Category.CVE, client)

    assert result.score == 6.5
    assert result.summary == "Balanced view."
    assert result.detail.get("council_mode") is True
    assert call_count == 11  # 5 advisors + 5 reviewers + 1 chairman

@pytest.mark.asyncio
async def test_council_handles_chairman_bad_json():
    from app.worker.council import run_council
    from app.worker.ai_client import AIClient
    from app.models.finding import Category

    config = {"provider": "openwebui", "base_url": "http://x", "api_key": "", "model_name": "m"}
    client = AIClient(config)

    call_count = 0
    async def mock_complete(prompt, system=""):
        nonlocal call_count
        call_count += 1
        if call_count <= 10:
            return '{"score": 5.0, "summary": "ok", "findings": {}}'
        return "The chairman cannot decide."  # bad JSON

    client.complete = mock_complete
    result = await run_council({"product": "X"}, Category.VENDOR_TRUST, client)
    assert result.score == 5.0  # fallback average of advisor scores
```

- [ ] **Step 2: Create `backend/app/worker/council.py`**

```python
import asyncio
import json
from app.worker.ai_client import AIClient
from app.worker.modules.base import ModuleResult
from app.worker.scoring import score_to_rag
from app.models.finding import Category

ADVISORS = [
    ("threat_modeler", "You are The Threat Modeler. Think like an attacker. What could be exploited? What is the worst-case abuse scenario? Focus on attack vectors, exploit likelihood, and impact severity. Be direct and specific. 150-300 words."),
    ("compliance_officer", "You are The Compliance Officer. Apply GDPR, SOC2, ISO27001, Cyber Essentials, UK Defence Cyber (CE+, DEFCON 658, DCPP Cyber Security Model) lenses. What would an auditor flag? What compliance gaps are present? 150-300 words."),
    ("risk_analyst", "You are The Risk Analyst. Quantify and contextualise risk. How likely is this to cause a real security incident? What is the impact if it does? Provide likelihood × impact reasoning. 150-300 words."),
    ("devils_advocate", "You are The Devil's Advocate. Challenge vendor claims and marketing language. What is being overstated, greenwashed, or left out? What does the fine print say that the headline obscures? 150-300 words."),
    ("pragmatist", "You are The Pragmatist. What does this mean in practice for an organisation deploying this product? What mitigations are feasible? What is the realistic day-to-day risk? 150-300 words."),
]

REVIEWER_PROMPT = """You are reviewing 5 independent security advisor responses to this question.
Question: {question}

{responses}

Answer these three questions concisely:
1. Which response is strongest and why? (name the advisor)
2. Which response has the biggest blind spot? What is missing?
3. What did ALL five responses miss that should be considered?

Under 200 words. Be direct."""

CHAIRMAN_SYSTEM = """You are the Chairman synthesising a security council review.
Produce a final JSON verdict. Schema:
{{"score": <float 0-10>, "summary": "<2-3 sentences synthesising all perspectives>", "findings": {{"where_council_agrees": "...", "where_council_clashes": "...", "blind_spots_caught": "...", "council": true}}}}
Base score on the weighted consensus of advisor positions. Respond with JSON only."""

async def _run_advisor(name: str, system: str, question: str, client: AIClient) -> tuple[str, str]:
    response = await client.complete(question, system=system)
    return name, response

async def _run_reviewer(question: str, advisor_responses: dict, client: AIClient) -> str:
    letters = ["A", "B", "C", "D", "E"]
    names = list(advisor_responses.keys())
    responses_text = "\n\n".join(
        f"**Response {letters[i]} ({names[i]}):**\n{advisor_responses[names[i]]}"
        for i in range(len(names))
    )
    prompt = REVIEWER_PROMPT.format(question=question, responses=responses_text)
    return await client.complete(prompt)

async def run_council(raw_data: dict, category: Category, client: AIClient) -> ModuleResult:
    question = f"Analyse this security assessment data for category '{category.value}':\n{json.dumps(raw_data, indent=2)}"

    # Step 1: 5 advisors in parallel
    advisor_tasks = [_run_advisor(name, system, question, client) for name, system in ADVISORS]
    advisor_results = await asyncio.gather(*advisor_tasks)
    advisor_responses = dict(advisor_results)

    # Step 2: 5 peer reviewers in parallel
    review_tasks = [_run_reviewer(question, advisor_responses, client) for _ in ADVISORS]
    reviews = await asyncio.gather(*review_tasks)

    # Step 3: Chairman synthesis
    chairman_context = question + "\n\nAdvisor responses:\n"
    for name, resp in advisor_responses.items():
        chairman_context += f"\n**{name}:**\n{resp}\n"
    chairman_context += "\n\nPeer reviews:\n" + "\n---\n".join(reviews)

    chairman_response = await client.complete(chairman_context, system=CHAIRMAN_SYSTEM)

    try:
        clean = chairman_response.strip().strip("```json").strip("```").strip()
        data = json.loads(clean)
        score = float(data.get("score", 5.0))
        summary = data.get("summary", "")
        findings = data.get("findings", {})
    except json.JSONDecodeError:
        # Fallback: average advisor scores if chairman JSON fails
        advisor_scores = []
        for resp in advisor_responses.values():
            try:
                d = json.loads(resp.strip().strip("```json").strip("```").strip())
                advisor_scores.append(float(d.get("score", 5.0)))
            except (json.JSONDecodeError, ValueError):
                advisor_scores.append(5.0)
        score = round(sum(advisor_scores) / len(advisor_scores), 2)
        summary = "Council synthesis (chairman fallback — see detail for advisor responses)."
        findings = {}

    findings["council_mode"] = True
    findings["advisor_responses"] = advisor_responses
    findings["peer_reviews"] = reviews
    findings["chairman_raw"] = chairman_response

    return ModuleResult(
        score=score,
        rag=score_to_rag(score),
        summary=summary,
        detail=findings,
    )
```

- [ ] **Step 3: Run council tests**

```bash
cd backend && python -m pytest ../tests/test_council.py -v
```

Expected: 2 PASS

- [ ] **Step 4: Commit**

```bash
git add backend/app/worker/council.py tests/test_council.py
git commit -m "feat: Deep Review council mode (5 advisors, peer review, chairman)"
```

---

### Task 17: Celery tasks and full assessment orchestration

**Files:**
- Create: `backend/app/worker/tasks.py`

- [ ] **Step 1: Create `backend/app/worker/tasks.py`**

```python
import asyncio
import uuid
from app.worker.celery_app import celery_app
from app.worker.db import worker_db, run_async
from app.worker.ai_client import get_ai_client_from_db
from app.worker.product_lookup import resolve_product
from app.worker.scoring import aggregate_scores, score_to_rag, derive_recommendation, DEFAULT_WEIGHTS
from app.worker.council import run_council
from app.models.assessment import Assessment, AssessmentStatus, ReviewMode
from app.models.finding import AssessmentFinding, Category
from app.models.product_confirmation import ProductConfirmation
from sqlalchemy import select

ALL_MODULE_CLASSES = None  # lazy import to avoid circular deps at task registration

def _load_modules():
    global ALL_MODULE_CLASSES
    if ALL_MODULE_CLASSES is None:
        from app.worker.modules.vendor_trust import VendorTrustModule
        from app.worker.modules.cve import CVEModule
        from app.worker.modules.maintenance import MaintenanceModule
        from app.worker.modules.dependency import DependencyModule
        from app.worker.modules.encryption import EncryptionModule
        from app.worker.modules.logging_module import LoggingModule
        from app.worker.modules.data_exfiltration import DataExfiltrationModule
        from app.worker.modules.third_party import ThirdPartyModule
        ALL_MODULE_CLASSES = [
            VendorTrustModule, CVEModule, MaintenanceModule, DependencyModule,
            EncryptionModule, LoggingModule, DataExfiltrationModule, ThirdPartyModule,
        ]
    return ALL_MODULE_CLASSES

async def _run_assessment_async(assessment_id: str):
    ai_client = await get_ai_client_from_db()

    async with worker_db() as db:
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()
        if not assessment:
            return

        # Product lookup step (name-only input)
        if assessment.input_type.value == "name" and assessment.status == AssessmentStatus.PENDING:
            suggestion = await resolve_product(assessment.product_name, ai_client)
            confirmation = ProductConfirmation(
                assessment_id=assessment.id,
                ai_suggested_name=suggestion.get("name", assessment.product_name),
                ai_suggested_vendor=suggestion.get("vendor", "Unknown"),
                ai_suggested_url=suggestion.get("url", ""),
            )
            db.add(confirmation)
            assessment.status = AssessmentStatus.CONFIRMING
            await db.commit()
            return  # Wait for user confirmation via API

        # Analysis phase
        assessment.status = AssessmentStatus.RUNNING
        await db.commit()

    # Run all 8 modules (outside the DB transaction to allow parallelism)
    module_classes = _load_modules()
    async with worker_db() as db:
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()

    tasks = []
    for ModuleClass in module_classes:
        module = ModuleClass(assessment, ai_client)
        if assessment.review_mode == ReviewMode.DEEP_REVIEW:
            async def run_with_council(m=module):
                std_result = await m.run()
                council_result = await run_council(std_result.detail, Category(m.category), ai_client)
                return m.category, council_result
            tasks.append(run_with_council())
        else:
            async def run_standard(m=module):
                result = await m.run()
                return m.category, result
            tasks.append(run_standard())

    module_results = await asyncio.gather(*tasks)

    # Persist findings
    scores = {}
    async with worker_db() as db:
        for category_str, module_result in module_results:
            category = Category(category_str)
            finding = AssessmentFinding(
                assessment_id=uuid.UUID(assessment_id),
                category=category,
                score=module_result.score,
                rag=module_result.rag,
                summary=module_result.summary,
                detail=module_result.detail,
            )
            db.add(finding)
            scores[category_str] = module_result.score

        # Compute overall score
        weight_map = {k.value: v for k, v in DEFAULT_WEIGHTS.items()}
        overall_score = aggregate_scores(scores, weight_map)
        overall_rag = score_to_rag(overall_score)
        recommendation = derive_recommendation(overall_rag)

        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()
        assessment.overall_score = overall_score
        assessment.overall_rag = overall_rag
        assessment.recommendation = recommendation
        assessment.status = AssessmentStatus.COMPLETE
        await db.commit()

@celery_app.task(name="app.worker.tasks.run_assessment", bind=True, max_retries=2)
def run_assessment(self, assessment_id: str):
    try:
        run_async(_run_assessment_async(assessment_id))
    except Exception as exc:
        run_async(_mark_failed(assessment_id))
        raise self.retry(exc=exc, countdown=30)

@celery_app.task(name="app.worker.tasks.run_analysis")
def run_analysis(assessment_id: str):
    run_async(_run_assessment_async(assessment_id))

async def _mark_failed(assessment_id: str):
    async with worker_db() as db:
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
        assessment = result.scalar_one_or_none()
        if assessment:
            assessment.status = AssessmentStatus.FAILED
            await db.commit()
```

- [ ] **Step 2: Commit**

```bash
git add backend/app/worker/tasks.py
git commit -m "feat: Celery assessment orchestration task"
```

---

### Task 18: PDF generation

**Files:**
- Create: `backend/app/pdf/generator.py`
- Create: `backend/app/pdf/templates/report.html.j2`
- Create: `backend/app/api/pdf.py`
- Modify: `backend/app/main.py`
- Test: `tests/test_pdf.py`

- [ ] **Step 1: Create `backend/app/pdf/templates/report.html.j2`**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<style>
  @page { size: A4; margin: 2cm; }
  body { font-family: Arial, sans-serif; font-size: 10pt; color: #222; }
  h1 { font-size: 20pt; color: #1a3a5c; margin-bottom: 4pt; }
  h2 { font-size: 13pt; color: #1a3a5c; border-bottom: 1px solid #ccc; padding-bottom: 4pt; }
  h3 { font-size: 11pt; margin-bottom: 4pt; }
  .header { background: #1a3a5c; color: white; padding: 20pt; margin: -2cm -2cm 20pt -2cm; }
  .header h1 { color: white; }
  .meta { font-size: 9pt; color: #aaa; }
  .score-big { font-size: 36pt; font-weight: bold; }
  .green { color: #2d8a3e; } .amber { color: #b86200; } .red { color: #c0392b; }
  .badge { display: inline-block; padding: 2pt 8pt; border-radius: 10pt; font-size: 9pt; font-weight: bold; }
  .badge-green { background: #d4edda; color: #2d8a3e; }
  .badge-amber { background: #fff3cd; color: #b86200; }
  .badge-red { background: #f8d7da; color: #c0392b; }
  .module { page-break-inside: avoid; margin-bottom: 16pt; padding: 10pt; border: 1pt solid #ddd; border-radius: 4pt; }
  .score-bar-bg { background: #eee; height: 8pt; border-radius: 4pt; }
  .score-bar-fill { height: 8pt; border-radius: 4pt; }
  table { width: 100%; border-collapse: collapse; font-size: 9pt; }
  td, th { padding: 4pt 6pt; border: 0.5pt solid #ddd; }
  th { background: #f5f5f5; }
  .page-break { page-break-after: always; }
</style>
</head>
<body>

<div class="header">
  <h1>{{ assessment.product_name }}</h1>
  <div class="meta">Security Posture Assessment · {{ assessment.created_at.strftime('%d %b %Y') }}</div>
  <div class="meta">Submitted by: {{ submitted_by_name }} · Assessment ID: {{ assessment.id }}</div>
</div>

<!-- Overall score -->
<table style="margin-bottom:16pt;">
  <tr>
    <td style="width:60%;vertical-align:top;">
      <h2 style="border:none;margin-top:0;">Executive Summary</h2>
      <p>{{ executive_summary }}</p>
      {% if analyst_notes %}
      <h3>Conditions / Analyst Notes</h3>
      <p>{{ analyst_notes }}</p>
      {% endif %}
    </td>
    <td style="text-align:center;vertical-align:middle;width:40%;">
      <div class="score-big {{ overall_rag }}">{{ "%.1f"|format(assessment.overall_score) }}</div>
      <div style="font-size:9pt;color:#888;">/10</div>
      <div class="badge badge-{{ overall_rag }}" style="margin-top:6pt;">
        {{ recommendation_label }}
      </div>
    </td>
  </tr>
</table>

<!-- Category scores table -->
<h2>Category Scores</h2>
<table>
  <tr><th>Category</th><th>Score</th><th>Status</th><th>Summary</th></tr>
  {% for finding in findings %}
  <tr>
    <td>{{ finding.category.value.replace('_', ' ').title() }}</td>
    <td class="{{ finding.rag.value }}"><strong>{{ "%.1f"|format(finding.score) }}</strong></td>
    <td><span class="badge badge-{{ finding.rag.value }}">{{ finding.rag.value.upper() }}</span></td>
    <td>{{ finding.summary[:120] }}{% if finding.summary|length > 120 %}…{% endif %}</td>
  </tr>
  {% endfor %}
</table>

<div class="page-break"></div>

<!-- Per-module detail pages -->
{% for finding in findings %}
<div class="module">
  <h2>{{ finding.category.value.replace('_', ' ').title() }}</h2>
  <div>
    <strong>Score:</strong>
    <span class="{{ finding.rag.value }}">{{ "%.1f"|format(finding.score) }}/10</span>
    &nbsp;
    <span class="badge badge-{{ finding.rag.value }}">{{ finding.rag.value.upper() }}</span>
  </div>
  <p>{{ finding.summary }}</p>
  {% if finding.analyst_notes %}
  <p><strong>Analyst notes:</strong> {{ finding.analyst_notes }}</p>
  {% endif %}
  <h3>Findings Detail</h3>
  {% for key, value in finding.detail.items() %}
  {% if key not in ('ai_response', 'advisor_responses', 'peer_reviews', 'chairman_raw') %}
  <p><strong>{{ key.replace('_', ' ').title() }}:</strong>
  {% if value is mapping %}{{ value | tojson(indent=2) }}
  {% elif value is iterable and value is not string %}{{ value | join(', ') }}
  {% else %}{{ value }}{% endif %}</p>
  {% endif %}
  {% endfor %}
</div>
{% if not loop.last %}<div class="page-break"></div>{% endif %}
{% endfor %}

<div class="page-break"></div>
<h2>Methodology</h2>
<p>This assessment was produced using SecurityChecker, an AI-driven security posture analysis tool.
Analysis covers eight categories: Vendor Trust, CVE &amp; Vulnerability History, Maintenance &amp; Activity,
Dependency Risk, Encryption, Logging &amp; Monitoring, Data Exfiltration Risk, and Third-party Integrations.
{% if assessment.review_mode.value == 'deep_review' %}
This assessment used Deep Review mode: each category was analysed by a five-advisor security council
(Threat Modeler, Compliance Officer, Risk Analyst, Devil's Advocate, Pragmatist) with peer review and
chairman synthesis.
{% endif %}
Scores are weighted and aggregated to produce an overall score. This report is provided for informational
purposes as part of an internal software approval process. It does not constitute a formal security audit.</p>
<p style="font-size:8pt;color:#888;">Generated: {{ now }} · Assessment ID: {{ assessment.id }}</p>

</body>
</html>
```

- [ ] **Step 2: Create `backend/app/pdf/generator.py`**

```python
from datetime import datetime, timezone
from jinja2 import Environment, PackageLoader, select_autoescape
from weasyprint import HTML
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid

from app.models.assessment import Assessment, RAGStatus, Recommendation
from app.models.finding import AssessmentFinding
from app.models.user import User

RECOMMENDATION_LABELS = {
    Recommendation.APPROVE: "Approve",
    Recommendation.CONDITIONAL: "Conditional Approval",
    Recommendation.REJECT: "Reject",
}

def _make_executive_summary(assessment: Assessment, findings: list) -> str:
    rag_counts = {"green": 0, "amber": 0, "red": 0}
    for f in findings:
        rag_counts[f.rag.value] += 1
    return (
        f"{assessment.product_name} received an overall score of "
        f"{assessment.overall_score:.1f}/10 ({assessment.overall_rag.value.upper()}). "
        f"Category breakdown: {rag_counts['green']} green, "
        f"{rag_counts['amber']} amber, {rag_counts['red']} red."
    )

async def generate_pdf(assessment_id: uuid.UUID, db: AsyncSession) -> bytes:
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise ValueError(f"Assessment {assessment_id} not found")

    findings_result = await db.execute(
        select(AssessmentFinding).where(AssessmentFinding.assessment_id == assessment_id)
        .order_by(AssessmentFinding.category)
    )
    findings = list(findings_result.scalars().all())

    user_result = await db.execute(select(User).where(User.id == assessment.submitted_by))
    user = user_result.scalar_one_or_none()
    submitted_by_name = user.full_name if user else "Unknown"

    analyst_notes = " | ".join(
        f.analyst_notes for f in findings if f.analyst_notes
    )

    env = Environment(
        loader=PackageLoader("app.pdf", "templates"),
        autoescape=select_autoescape(["html"]),
    )
    template = env.get_template("report.html.j2")
    html_content = template.render(
        assessment=assessment,
        findings=findings,
        submitted_by_name=submitted_by_name,
        overall_rag=assessment.overall_rag.value,
        recommendation_label=RECOMMENDATION_LABELS.get(assessment.recommendation, ""),
        executive_summary=_make_executive_summary(assessment, findings),
        analyst_notes=analyst_notes,
        now=datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    )

    return HTML(string=html_content).write_pdf()
```

- [ ] **Step 3: Create `backend/app/api/pdf.py`**

```python
import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Role
from app.models.assessment import Assessment, AssessmentStatus
from app.core.rbac import require_role
from app.pdf.generator import generate_pdf

router = APIRouter(tags=["pdf"])

@router.get("/assessments/{assessment_id}/pdf")
async def download_pdf(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.VIEWER)),
):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status != AssessmentStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Assessment is not complete")

    pdf_bytes = await generate_pdf(assessment_id, db)
    filename = f"security-assessment-{assessment.product_name.lower().replace(' ', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
```

- [ ] **Step 4: Register PDF router in `backend/app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api import auth, assessments, users, ai_config, pdf

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
app.include_router(pdf.router, prefix="/api/v1")
```

- [ ] **Step 5: Write PDF test**

Create `tests/test_pdf.py`:

```python
import pytest
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

@pytest.mark.asyncio
async def test_pdf_endpoint_requires_complete_status(client, viewer_user, analyst_user, db):
    from app.models.assessment import Assessment, InputType, AssessmentStatus, ReviewMode
    from tests.conftest import login

    a = Assessment(
        product_name="TestApp",
        input_type=InputType.NAME,
        status=AssessmentStatus.RUNNING,
        review_mode=ReviewMode.STANDARD,
        submitted_by=analyst_user.id,
    )
    db.add(a)
    await db.commit()

    token = await login(client, "viewer@test.com")
    r = await client.get(
        f"/api/v1/assessments/{a.id}/pdf",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r.status_code == 400

@pytest.mark.asyncio
async def test_pdf_endpoint_returns_pdf_for_complete_assessment(client, analyst_user, db):
    from app.models.assessment import Assessment, InputType, AssessmentStatus, ReviewMode, RAGStatus, Recommendation
    from app.models.finding import AssessmentFinding, Category
    from tests.conftest import login

    a = Assessment(
        product_name="Slack",
        input_type=InputType.URL,
        product_url="https://slack.com",
        status=AssessmentStatus.COMPLETE,
        review_mode=ReviewMode.STANDARD,
        overall_score=8.0,
        overall_rag=RAGStatus.GREEN,
        recommendation=Recommendation.APPROVE,
        submitted_by=analyst_user.id,
    )
    db.add(a)
    await db.flush()

    for cat in Category:
        db.add(AssessmentFinding(
            assessment_id=a.id, category=cat,
            score=8.0, rag=RAGStatus.GREEN,
            summary="All good.", detail={},
        ))
    await db.commit()

    token = await login(client, "analyst@test.com")
    with patch("app.pdf.generator.HTML") as mock_html:
        mock_html.return_value.write_pdf.return_value = b"%PDF-mock"
        r = await client.get(
            f"/api/v1/assessments/{a.id}/pdf",
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 200
    assert r.headers["content-type"] == "application/pdf"
```

- [ ] **Step 6: Run all tests**

```bash
cd backend && python -m pytest ../tests/ -v --tb=short
```

Expected: All PASS

- [ ] **Step 7: Commit**

```bash
git add backend/app/pdf/ backend/app/api/pdf.py backend/app/main.py tests/test_pdf.py
git commit -m "feat: PDF report generation (WeasyPrint + Jinja2 template)"
```

---

**Plan 2 complete.** The analysis engine now has:
- Celery worker with full assessment orchestration
- AIClient abstraction (OpenWebUI / Ollama / Gemini)
- Product lookup with AI product identity resolution
- All 8 analysis modules (Standard mode, with NVD API, GitHub API, Trivy/pip-audit)
- Deep Review council mode (5 advisors + peer review + chairman)
- Score aggregation and RAG/recommendation derivation
- PDF report generation with Jinja2 template

**Continue with:** `2026-06-03-security-checker-plan-3-frontend.md`
