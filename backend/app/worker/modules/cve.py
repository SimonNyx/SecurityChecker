import json
import httpx
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing CVE history for software approval.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"total_cves": 0, "critical": 0, "high": 0, "medium": 0, "low": 0, "recent_cves": [...], "avg_patch_days": null, "unpatched_critical": 0}}

Scoring principles:
- Raw CVE count is NOT the primary signal. High-profile, widely-deployed products (browsers, enterprise platforms, OS components) attract more CVEs because they are more scrutinised and more targeted — this is expected and normal.
- PATCH RESPONSIVENESS is the most important factor: how quickly are vulnerabilities fixed once discovered? A product with 200 CVEs patched within 14 days on average is more trustworthy than one with 10 CVEs left unpatched for 6 months.
- Positive signals that RAISE the score: active security team, coordinated disclosure programme, bug bounty, rapid patch cadence (under 30 days average), CVEs resolved before or shortly after public disclosure, track record of proactive patching.
- Negative signals that LOWER the score: unpatched critical/high CVEs, slow patch times (90+ days), history of ignoring reports, CVEs actively exploited in the wild with no patch, vendor silence on disclosures.

Score rubric:
9-10: Strong patch responsiveness (avg <14 days), no unpatched criticals, proactive disclosure programme — high CVE count acceptable if all addressed promptly.
7-8: Good responsiveness (avg <30 days), minor unpatched lows only, or low-CVE product with good track record.
5-6: Mixed — some delayed patches (30-90 days) or a few unpatched medium/high CVEs, no clear disclosure programme.
3-4: Poor responsiveness (90+ days average), multiple unpatched high CVEs, or evidence of ignoring reports.
0-2: Critical CVEs actively unpatched, product abandoned, or history of dismissing security reports."""

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

Assess the following and weight your score accordingly:
1. Patch responsiveness — average time from CVE disclosure to patch release. This is the most important factor.
2. Product exposure context — is this a high-profile target (browser, enterprise platform, OS component) where a higher CVE count is expected and normal?
3. Active security programme — evidence of bug bounty, coordinated disclosure, dedicated security team.
4. Unpatched CVEs — are any critical or high CVEs currently unpatched or actively exploited?
5. Trend — is the patch cadence improving or worsening over recent releases?

Do not penalise high CVE volume alone if patch responsiveness is strong. A large, widely-used product that patches quickly should score higher than a niche product with few CVEs but poor responsiveness.
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
