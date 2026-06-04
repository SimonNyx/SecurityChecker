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
