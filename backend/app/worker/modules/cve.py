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
