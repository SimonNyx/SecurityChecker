import json
import subprocess
import tempfile
import os
from app.worker.modules.base import BaseModule, ModuleResult
from app.worker.scoring import score_to_rag

SYSTEM = """You are a security analyst assessing software dependency risk.
Respond with JSON only, no markdown. Schema:
{"score": <float 0-10>, "summary": "<1-3 sentences>", "findings": {"vulnerable_deps": 0, "critical_vulns": 0, "high_vulns": 0, "outdated_deps": 0, "total_deps": 0, "scanner_used": "...", "notable_issues": [...]}}
Score rubric: 9-10=no vulnerable deps; 7-8=low severity only, all outdated non-critical; 5-6=some medium vulns; 3-4=high vulns present; 0-2=critical vulns in dependencies or known compromised packages."""

def _run_trivy(repo_path: str) -> dict:
    try:
        result = subprocess.run(
            ["trivy", "fs", "--format", "json", "--quiet", repo_path],
            capture_output=True, text=True, timeout=120
        )
        return json.loads(result.stdout) if result.stdout else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return {}

def _run_pip_audit(repo_path: str) -> dict:
    req_file = os.path.join(repo_path, "requirements.txt")
    if not os.path.exists(req_file):
        return {}
    try:
        result = subprocess.run(
            ["pip-audit", "--format", "json", "-r", req_file],
            capture_output=True, text=True, timeout=60
        )
        return json.loads(result.stdout) if result.stdout else {}
    except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
        return {}

def _clone_repo(repo_url: str, target_dir: str) -> bool:
    try:
        result = subprocess.run(
            ["git", "clone", "--depth", "1", repo_url, target_dir],
            capture_output=True, timeout=120
        )
        return result.returncode == 0
    except (FileNotFoundError, subprocess.TimeoutExpired):
        return False

class DependencyModule(BaseModule):
    category = "dependency"

    async def run(self) -> ModuleResult:
        scan_data = {}
        scanner_used = "ai_synthesis"

        if self.assessment.repo_url:
            with tempfile.TemporaryDirectory() as tmpdir:
                repo_dir = os.path.join(tmpdir, "repo")
                if _clone_repo(self.assessment.repo_url, repo_dir):
                    trivy = _run_trivy(repo_dir)
                    pip = _run_pip_audit(repo_dir)
                    scan_data = {"trivy": trivy, "pip_audit": pip}
                    scanner_used = "trivy+pip_audit"

        prompt = f"""Assess dependency risk for: {self.assessment.product_name}
Repo: {self.assessment.repo_url or 'not provided'}
Scanner results: {json.dumps(scan_data) if scan_data else 'No repo scan available — use AI synthesis from public information.'}

Identify vulnerable, outdated, or risky dependencies. Note any known supply-chain incidents.
Return JSON only."""

        response = await self._ask_ai(prompt, system=SYSTEM)
        try:
            clean = response.strip().strip("```json").strip("```").strip()
            data = json.loads(clean)
        except json.JSONDecodeError:
            data = {"score": 5.0, "summary": response[:300], "findings": {}}

        if "scanner_used" not in data.get("findings", {}):
            data.setdefault("findings", {})["scanner_used"] = scanner_used

        score = float(data.get("score", 5.0))
        return ModuleResult(
            score=score,
            rag=score_to_rag(score),
            summary=data.get("summary", ""),
            detail={"scan": scan_data, "findings": data.get("findings", {}), "ai_response": response},
        )
