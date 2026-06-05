import os
import re
from datetime import datetime
from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML

TEMPLATE_DIR = os.path.join(os.path.dirname(__file__), "templates")
_env = Environment(loader=FileSystemLoader(TEMPLATE_DIR), autoescape=True)

RAG_COLOURS = {
    "green": "#22c55e",
    "amber": "#f59e0b",
    "red": "#ef4444",
}

RECOMMENDATION_LABELS = {
    "approve": "APPROVE",
    "conditional": "CONDITIONAL APPROVAL",
    "reject": "REJECT",
}

RECOMMENDATION_COLOURS = {
    "approve": "#22c55e",
    "conditional": "#f59e0b",
    "reject": "#ef4444",
}

SECTION_PATTERNS = [
    (re.compile(r'overall\s+posture', re.I), 'Overall Posture'),
    (re.compile(r'key\s+strengths?', re.I), 'Key Strengths'),
    (re.compile(r'key\s+concerns?', re.I), 'Key Concerns'),
    (re.compile(r'recommended?\s+next\s+steps?', re.I), 'Recommended Next Steps'),
]


def _parse_exec_summary(text: str) -> list[dict]:
    """Return [{heading, lines, is_list}] for each section."""
    sections = []
    current = None
    for raw in text.split('\n'):
        line = re.sub(r'^[#*\s]+|[#*\s]+$', '', raw).strip()
        if not line:
            continue
        matched = None
        clean = line.lower()
        for pattern, label in SECTION_PATTERNS:
            if pattern.search(clean):
                matched = label
                break
        if matched:
            if current:
                sections.append(current)
            current = {'heading': matched, 'lines': []}
        elif current:
            current['lines'].append(line)
    if current:
        sections.append(current)
    for s in sections:
        s['is_list'] = bool(s['lines']) and s['lines'][0].startswith('-')
        s['lines'] = [l.lstrip('- ').strip() if s['is_list'] else l for l in s['lines']]
    return sections


CATEGORY_LABELS = {
    "vendor_trust": "Vendor Trust",
    "cve": "CVE History",
    "maintenance": "Maintenance",
    "dependency": "Dependency Risk",
    "encryption": "Encryption",
    "logging": "Logging & Monitoring",
    "data_exfiltration": "Data Exfiltration Risk",
    "third_party": "Third-Party Integrations",
}


def generate_pdf(assessment) -> bytes:
    template = _env.get_template("report.html")
    findings_data = [
        {
            "category": CATEGORY_LABELS.get(f.category.value, f.category.value),
            "score": round(f.score, 1),
            "rag": f.rag.value,
            "rag_colour": RAG_COLOURS.get(f.rag.value, "#999"),
            "summary": f.summary,
        }
        for f in sorted(assessment.findings, key=lambda x: x.category.value)
    ]

    rec = assessment.recommendation.value if assessment.recommendation else "conditional"

    context = {
        "product_name": assessment.product_name,
        "product_url": assessment.product_url or "—",
        "repo_url": assessment.repo_url or "—",
        "review_mode": "Deep Review" if assessment.review_mode.value == "deep_review" else "Standard",
        "overall_score": round(assessment.overall_score, 1) if assessment.overall_score is not None else "—",
        "overall_rag": assessment.overall_rag.value if assessment.overall_rag else "amber",
        "overall_rag_colour": RAG_COLOURS.get(assessment.overall_rag.value if assessment.overall_rag else "amber", "#999"),
        "recommendation": RECOMMENDATION_LABELS.get(rec, rec.upper()),
        "recommendation_colour": RECOMMENDATION_COLOURS.get(rec, "#999"),
        "findings": findings_data,
        "executive_summary": assessment.executive_summary or "",
        "exec_sections": _parse_exec_summary(assessment.executive_summary) if assessment.executive_summary else [],
        "submitted_by_name": assessment.submitted_by_name or "—",
        "generated_at": datetime.utcnow().strftime("%d/%m/%Y %H:%M UTC"),
    }

    html_content = template.render(**context)
    return HTML(string=html_content).write_pdf()
