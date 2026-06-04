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
