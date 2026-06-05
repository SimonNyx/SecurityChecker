"""Fix executive summaries stored as raw JSON — run once."""
import asyncio
import json
import re
from sqlalchemy import select
from app.worker.db import worker_db
from app.models.assessment import Assessment


def _repair_json(text: str) -> str:
    """Fix common LLM JSON error: missing ] before closing }."""
    # Count unclosed arrays vs objects
    try:
        json.loads(text)
        return text
    except json.JSONDecodeError:
        pass
    # Try adding ] before final }
    if text.rstrip().endswith('"}'):
        candidate = text.rstrip()[:-1] + "]}"
        try:
            json.loads(candidate)
            return candidate
        except json.JSONDecodeError:
            pass
    return text


def format_exec_summary(raw: str) -> str:
    text = raw.strip()
    text = re.sub(r'^```[a-z]*\n?', '', text)
    text = re.sub(r'\n?```$', '', text)
    text = text.strip()
    text = _repair_json(text)
    data = json.loads(text)
    lines = []
    if data.get("overall_posture"):
        lines.append("OVERALL POSTURE")
        lines.append(data["overall_posture"].strip())
        lines.append("")
    if data.get("key_strengths"):
        lines.append("KEY STRENGTHS")
        for item in data["key_strengths"]:
            lines.append(f"- {item.strip()}")
        lines.append("")
    if data.get("key_concerns"):
        lines.append("KEY CONCERNS")
        for item in data["key_concerns"]:
            lines.append(f"- {item.strip()}")
        lines.append("")
    if data.get("next_steps"):
        lines.append("RECOMMENDED NEXT STEPS")
        for item in data["next_steps"]:
            lines.append(f"- {item.strip()}")
    return "\n".join(lines).strip()


async def fix():
    async with worker_db() as db:
        result = await db.execute(select(Assessment))
        fixed = 0
        for a in result.scalars().all():
            if a.executive_summary and a.executive_summary.strip().startswith("{"):
                try:
                    formatted = format_exec_summary(a.executive_summary)
                    a.executive_summary = formatted
                    print(f"Fixed: {a.product_name}")
                    fixed += 1
                except Exception as e:
                    print(f"Failed {a.product_name}: {e}")
        await db.commit()
        print(f"Done — fixed {fixed} assessments")


asyncio.run(fix())
