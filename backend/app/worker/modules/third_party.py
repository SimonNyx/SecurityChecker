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
