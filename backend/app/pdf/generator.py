import os
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
        "generated_at": datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
    }

    html_content = template.render(**context)
    return HTML(string=html_content).write_pdf()
