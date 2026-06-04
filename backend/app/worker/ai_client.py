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

        # OpenWebUI uses /api/chat/completions; Ollama uses /v1/chat/completions
        path = "/v1/chat/completions" if self.provider == AIProvider.OLLAMA else "/api/chat/completions"
        async with httpx.AsyncClient(timeout=120) as http:
            resp = await http.post(
                f"{self.base_url}{path}",
                headers=headers,
                json={"model": self.model, "messages": messages},
            )
            resp.raise_for_status()
            return resp.json()["choices"][0]["message"]["content"]

    async def test_connection(self) -> dict:
        """Send a minimal ping to verify the AI provider is reachable and responsive."""
        try:
            response = await self.complete("Reply with the single word: ok", system="")
            return {"ok": True, "response": response[:100]}
        except httpx.ConnectError as e:
            return {"ok": False, "error": f"Cannot connect to {self.base_url}: {e}"}
        except httpx.HTTPStatusError as e:
            return {"ok": False, "error": f"HTTP {e.response.status_code}: {e.response.text[:200]}"}
        except Exception as e:
            return {"ok": False, "error": str(e)[:200]}

    async def _gemini_complete(self, prompt: str, system: str) -> str:
        full_prompt = f"{system}\n\n{prompt}" if system else prompt
        url = f"{self.base_url}/v1beta/models/{self.model}:generateContent"
        async with httpx.AsyncClient(timeout=120) as http:
            resp = await http.post(
                url,
                headers={"x-goog-api-key": self.api_key},
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
