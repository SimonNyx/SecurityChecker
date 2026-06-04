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
