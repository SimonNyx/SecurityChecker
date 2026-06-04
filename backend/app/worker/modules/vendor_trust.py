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
