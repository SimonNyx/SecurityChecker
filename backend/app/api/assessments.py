import uuid
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status

logger = logging.getLogger(__name__)
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Role
from app.models.assessment import Assessment, InputType, AssessmentStatus
from app.models.finding import AssessmentFinding, Category
from app.models.product_confirmation import ProductConfirmation
from app.schemas.assessment import AssessmentCreate, AssessmentOut, ProductConfirmRequest
from app.schemas.finding import FindingOut, FindingUpdate
from app.api.deps import get_current_user
from app.core.rbac import require_role
from app.core.audit import log_action
from app.worker.celery_app import celery_app

router = APIRouter(prefix="/assessments", tags=["assessments"])

def _derive_input_type(body: AssessmentCreate) -> InputType:
    if body.repo_url:
        return InputType.REPO
    if body.product_url:
        return InputType.URL
    return InputType.NAME

@router.get("", response_model=list[AssessmentOut])
async def list_assessments(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.VIEWER)),
    status_filter: str | None = None,
    skip: int = 0,
    limit: int = 50,
):
    q = select(Assessment).order_by(Assessment.created_at.desc()).offset(skip).limit(limit)
    if status_filter:
        q = q.where(Assessment.status == status_filter)
    result = await db.execute(q)
    return result.scalars().all()

@router.post("", response_model=AssessmentOut, status_code=status.HTTP_201_CREATED)
async def create_assessment(
    body: AssessmentCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ANALYST)),
):
    input_type = _derive_input_type(body)
    assessment = Assessment(
        product_name=body.product_name,
        product_url=body.product_url,
        repo_url=body.repo_url,
        input_type=input_type,
        review_mode=body.review_mode,
        submitted_by=current_user.id,
        status=AssessmentStatus.PENDING,
    )
    db.add(assessment)
    await db.commit()
    await db.refresh(assessment)
    await log_action(db, current_user.id, "submit_assessment", "assessment", assessment.id)
    await db.commit()

    try:
        celery_app.send_task("run_assessment", args=[str(assessment.id)])
    except Exception as e:
        logger.error(f"Failed to dispatch run_assessment for {assessment.id}: {e}")

    return assessment

@router.get("/{assessment_id}", response_model=AssessmentOut)
async def get_assessment(
    assessment_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.VIEWER)),
):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    return assessment

@router.post("/{assessment_id}/confirm-product", response_model=AssessmentOut)
async def confirm_product(
    assessment_id: uuid.UUID,
    body: ProductConfirmRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ANALYST)),
):
    result = await db.execute(select(Assessment).where(Assessment.id == assessment_id))
    assessment = result.scalar_one_or_none()
    if not assessment:
        raise HTTPException(status_code=404, detail="Assessment not found")
    if assessment.status != AssessmentStatus.CONFIRMING:
        raise HTTPException(status_code=400, detail="Assessment is not awaiting confirmation")

    conf_result = await db.execute(
        select(ProductConfirmation).where(ProductConfirmation.assessment_id == assessment_id)
    )
    confirmation = conf_result.scalar_one_or_none()
    if confirmation:
        confirmation.confirmed_by = current_user.id
        confirmation.confirmed_at = datetime.now(timezone.utc)

    assessment.product_name = body.confirmed_name
    assessment.product_url = body.confirmed_url or assessment.product_url
    assessment.status = AssessmentStatus.RUNNING
    await db.commit()
    await db.refresh(assessment)

    try:
        celery_app.send_task("run_analysis", args=[str(assessment_id)])
    except Exception as e:
        logger.error(f"Failed to dispatch run_analysis for {assessment_id}: {e}")

    return assessment

@router.put("/{assessment_id}/findings/{category}", response_model=FindingOut)
async def update_finding(
    assessment_id: uuid.UUID,
    category: Category,
    body: FindingUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ANALYST)),
):
    result = await db.execute(
        select(AssessmentFinding).where(
            AssessmentFinding.assessment_id == assessment_id,
            AssessmentFinding.category == category,
        )
    )
    finding = result.scalar_one_or_none()
    if not finding:
        raise HTTPException(status_code=404, detail="Finding not found")
    if body.analyst_notes is not None:
        finding.analyst_notes = body.analyst_notes
    if body.score is not None:
        finding.score = body.score
    finding.edited_by = current_user.id
    finding.edited_at = datetime.now(timezone.utc)
    await db.commit()
    await db.refresh(finding)
    await log_action(db, current_user.id, "edit_finding", "finding", finding.id,
                     {"category": category.value})
    await db.commit()
    return finding
