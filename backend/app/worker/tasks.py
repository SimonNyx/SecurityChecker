import uuid
import logging
from celery import shared_task
from sqlalchemy import select

from app.worker.celery_app import celery_app
from app.worker.db import worker_db, run_async
from app.worker.ai_client import get_ai_client_from_db
from app.worker.product_lookup import resolve_product
from app.worker.council import run_council
from app.worker.scoring import DEFAULT_WEIGHTS, aggregate_scores, score_to_rag, derive_recommendation
from app.models.assessment import Assessment, AssessmentStatus, ReviewMode
from app.models.finding import AssessmentFinding, Category
from app.worker.modules.vendor_trust import VendorTrustModule
from app.worker.modules.cve import CVEModule
from app.worker.modules.maintenance import MaintenanceModule
from app.worker.modules.dependency import DependencyModule
from app.worker.modules.encryption import EncryptionModule
from app.worker.modules.logging_module import LoggingModule
from app.worker.modules.data_exfiltration import DataExfiltrationModule
from app.worker.modules.third_party import ThirdPartyModule

logger = logging.getLogger(__name__)

MODULE_MAP = [
    (VendorTrustModule, Category.VENDOR_TRUST),
    (CVEModule, Category.CVE),
    (MaintenanceModule, Category.MAINTENANCE),
    (DependencyModule, Category.DEPENDENCY),
    (EncryptionModule, Category.ENCRYPTION),
    (LoggingModule, Category.LOGGING),
    (DataExfiltrationModule, Category.DATA_EXFILTRATION),
    (ThirdPartyModule, Category.THIRD_PARTY),
]


@celery_app.task(bind=True, name="run_assessment")
def run_assessment(self, assessment_id: str):
    """Main assessment orchestration task."""
    run_async(_run_assessment_async(assessment_id))


async def _run_assessment_async(assessment_id: str):
    assessment_uuid = uuid.UUID(assessment_id)

    async with worker_db() as db:
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_uuid))
        assessment = result.scalar_one_or_none()
        if not assessment:
            logger.error(f"Assessment {assessment_id} not found")
            return

        try:
            ai_client = await get_ai_client_from_db()

            # Product lookup / confirmation
            assessment.status = AssessmentStatus.CONFIRMING
            await db.commit()

            product_info = await resolve_product(assessment.product_name, ai_client)

            # Auto-confirm if confidence is high; otherwise wait for user confirmation
            if product_info.get("confidence") == "high":
                if not assessment.product_url and product_info.get("url"):
                    assessment.product_url = product_info["url"]
                assessment.status = AssessmentStatus.RUNNING
                await db.commit()
                await _run_modules(assessment_uuid, db, ai_client, assessment)
            else:
                # Leave in CONFIRMING — API's POST /confirm will trigger run_analysis task
                await db.commit()

        except Exception as e:
            logger.exception(f"Assessment {assessment_id} failed: {e}")
            async with worker_db() as err_db:
                r = await err_db.execute(select(Assessment).where(Assessment.id == assessment_uuid))
                a = r.scalar_one_or_none()
                if a:
                    a.status = AssessmentStatus.FAILED
                await err_db.commit()


@celery_app.task(bind=True, name="run_single_module")
def run_single_module(self, assessment_id: str, category_value: str):
    """Re-run a single analysis module, replace its finding, recompute overall score."""
    run_async(_run_single_module_async(assessment_id, category_value))


async def _run_single_module_async(assessment_id: str, category_value: str):
    assessment_uuid = uuid.UUID(assessment_id)
    target_category = Category(category_value)
    module_class = next((cls for cls, cat in MODULE_MAP if cat == target_category), None)
    if not module_class:
        logger.error(f"No module found for category {category_value}")
        return

    async with worker_db() as db:
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_uuid))
        assessment = result.scalar_one_or_none()
        if not assessment:
            return

        try:
            ai_client = await get_ai_client_from_db()
            module = module_class(assessment, ai_client)
            if assessment.review_mode == ReviewMode.DEEP_REVIEW:
                mod_result = await run_council(module)
            else:
                mod_result = await module.run()

            # Replace existing finding for this category
            existing = await db.execute(
                select(AssessmentFinding).where(
                    AssessmentFinding.assessment_id == assessment_uuid,
                    AssessmentFinding.category == target_category,
                )
            )
            finding = existing.scalar_one_or_none()
            if finding:
                finding.score = mod_result.score
                finding.rag = mod_result.rag
                finding.summary = mod_result.summary
                finding.detail = mod_result.detail
            else:
                db.add(AssessmentFinding(
                    assessment_id=assessment_uuid,
                    category=target_category,
                    score=mod_result.score,
                    rag=mod_result.rag,
                    summary=mod_result.summary,
                    detail=mod_result.detail,
                ))
            await db.commit()

            # Recompute overall from all current findings
            all_findings = (await db.execute(
                select(AssessmentFinding).where(AssessmentFinding.assessment_id == assessment_uuid)
            )).scalars().all()
            scores = {f.category.value: f.score for f in all_findings}
            weight_map = {k.value: v for k, v in DEFAULT_WEIGHTS.items()}
            overall = aggregate_scores(scores, weight_map)
            assessment.overall_score = overall
            assessment.overall_rag = score_to_rag(overall)
            assessment.recommendation = derive_recommendation(assessment.overall_rag)
            await db.commit()

        except Exception as e:
            logger.exception(f"Single module {category_value} failed for {assessment_uuid}: {e}")


@celery_app.task(bind=True, name="run_analysis")
def run_analysis(self, assessment_id: str):
    """Run all analysis modules for a confirmed assessment."""
    run_async(_run_analysis_async(assessment_id))


async def _run_analysis_async(assessment_id: str):
    assessment_uuid = uuid.UUID(assessment_id)
    async with worker_db() as db:
        result = await db.execute(select(Assessment).where(Assessment.id == assessment_uuid))
        assessment = result.scalar_one_or_none()
        if not assessment:
            return

        try:
            ai_client = await get_ai_client_from_db()
            assessment.status = AssessmentStatus.RUNNING
            await db.commit()
            await _run_modules(assessment_uuid, db, ai_client, assessment)
        except Exception as e:
            logger.exception(f"run_analysis {assessment_id} failed: {e}")
            assessment.status = AssessmentStatus.FAILED
            await db.commit()


async def _run_modules(assessment_uuid, db, ai_client, assessment):
    """Run all 8 modules and persist findings + overall score."""
    scores = {}

    for ModuleClass, category in MODULE_MAP:
        try:
            module = ModuleClass(assessment, ai_client)
            if assessment.review_mode == ReviewMode.DEEP_REVIEW:
                result = await run_council(module)
            else:
                result = await module.run()

            finding = AssessmentFinding(
                assessment_id=assessment_uuid,
                category=category,
                score=result.score,
                rag=result.rag,
                summary=result.summary,
                detail=result.detail,
            )
            db.add(finding)
            scores[category.value] = result.score

        except Exception as e:
            logger.error(f"Module {category.value} failed for {assessment_uuid}: {e}")
            # Add a failed finding so the assessment can still complete
            from app.models.assessment import RAGStatus
            finding = AssessmentFinding(
                assessment_id=assessment_uuid,
                category=category,
                score=0.0,
                rag=RAGStatus.RED,
                summary=f"Module failed: {str(e)[:200]}",
                detail={"error": str(e)},
            )
            db.add(finding)
            scores[category.value] = 0.0

    await db.commit()

    # Compute overall score
    weight_map = {k.value: v for k, v in DEFAULT_WEIGHTS.items()}
    overall = aggregate_scores(scores, weight_map)
    overall_rag = score_to_rag(overall)

    async with worker_db() as final_db:
        r = await final_db.execute(select(Assessment).where(Assessment.id == assessment_uuid))
        a = r.scalar_one_or_none()
        if a:
            a.overall_score = overall
            a.overall_rag = overall_rag
            a.recommendation = derive_recommendation(overall_rag)
            a.status = AssessmentStatus.COMPLETE
        await final_db.commit()
