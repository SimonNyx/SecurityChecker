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
