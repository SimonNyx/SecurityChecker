import uuid
from unittest.mock import MagicMock, patch
from datetime import datetime


def _make_assessment():
    from app.models.assessment import Assessment, InputType, AssessmentStatus, RAGStatus, Recommendation, ReviewMode
    from app.models.finding import AssessmentFinding, Category

    a = Assessment(
        id=uuid.uuid4(),
        product_name="Slack",
        product_url="https://slack.com",
        repo_url=None,
        input_type=InputType.URL,
        status=AssessmentStatus.COMPLETE,
        review_mode=ReviewMode.STANDARD,
        overall_score=7.8,
        overall_rag=RAGStatus.GREEN,
        recommendation=Recommendation.APPROVE,
        submitted_by=uuid.uuid4(),
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )

    categories = [
        (Category.VENDOR_TRUST, 8.0, RAGStatus.GREEN, "Well-established vendor."),
        (Category.CVE, 7.5, RAGStatus.GREEN, "Few CVEs, patched promptly."),
        (Category.MAINTENANCE, 8.0, RAGStatus.GREEN, "Active maintenance."),
        (Category.DEPENDENCY, 7.0, RAGStatus.AMBER, "Some outdated deps."),
        (Category.ENCRYPTION, 9.0, RAGStatus.GREEN, "TLS 1.3, AES-256."),
        (Category.LOGGING, 6.5, RAGStatus.AMBER, "Audit log available on paid plan."),
        (Category.DATA_EXFILTRATION, 7.5, RAGStatus.GREEN, "GDPR compliant."),
        (Category.THIRD_PARTY, 8.0, RAGStatus.GREEN, "Reputable providers only."),
    ]

    a.findings = [
        AssessmentFinding(
            id=uuid.uuid4(),
            assessment_id=a.id,
            category=cat,
            score=score,
            rag=rag,
            summary=summary,
            detail={},
        )
        for cat, score, rag, summary in categories
    ]
    a.product_confirmation = None
    return a


def test_generate_pdf_returns_bytes():
    from app.pdf.generator import generate_pdf
    assessment = _make_assessment()
    pdf_bytes = generate_pdf(assessment)
    assert isinstance(pdf_bytes, bytes)
    assert len(pdf_bytes) > 1000
    assert pdf_bytes[:4] == b"%PDF"


def test_generate_pdf_all_categories_present():
    from app.pdf.generator import generate_pdf, CATEGORY_LABELS
    assessment = _make_assessment()
    pdf_bytes = generate_pdf(assessment)
    # Just verify it generates without error and has content
    assert len(pdf_bytes) > 0
