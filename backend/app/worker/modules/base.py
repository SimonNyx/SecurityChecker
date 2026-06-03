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
        self._advisor_prefix: str = ""

    @abstractmethod
    async def run(self) -> ModuleResult:
        """Gather data and return a ModuleResult."""

    async def _ask_ai(self, prompt: str, system: str = "") -> str:
        effective_system = (self._advisor_prefix + "\n\n" + system).strip() if self._advisor_prefix else system
        return await self.ai.complete(prompt, effective_system)
