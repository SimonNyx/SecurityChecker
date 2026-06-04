import uuid
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Role
from app.models.assessment import Assessment, AssessmentStatus
from app.api.deps import get_current_user
from app.core.rbac import require_role
from app.pdf.generator import generate_pdf

router = APIRouter(prefix="/assessments", tags=["pdf"])


@router.get("/{assessment_id}/pdf")
async def download_pdf(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.VIEWER)),
):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status != AssessmentStatus.COMPLETE:
        raise HTTPException(status_code=400, detail="Assessment not yet complete")

    pdf_bytes = generate_pdf(assessment)
    filename = f"security-report-{assessment.product_name.lower().replace(' ', '-')}.pdf"
    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )
