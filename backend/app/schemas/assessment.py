import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.assessment import InputType, AssessmentStatus, RAGStatus, Recommendation, ReviewMode
from app.schemas.finding import FindingOut


class AssessmentRunOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    run_at: datetime
    run_by: uuid.UUID
    run_by_name: str | None = None
    review_mode: ReviewMode
    overall_score: float | None
    overall_rag: RAGStatus | None
    recommendation: Recommendation | None

class AssessmentCreate(BaseModel):
    product_name: str
    product_url: str | None = None
    repo_url: str | None = None
    review_mode: ReviewMode = ReviewMode.STANDARD
    project_scope: str | None = None

class ProductConfirmRequest(BaseModel):
    confirmed_name: str
    confirmed_vendor: str
    confirmed_url: str

class RerunRequest(BaseModel):
    review_mode: ReviewMode
    project_scope: str | None = None

class AssessmentOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    product_name: str
    product_url: str | None
    repo_url: str | None
    input_type: InputType
    status: AssessmentStatus
    review_mode: ReviewMode
    project_scope: str | None
    executive_summary: str | None
    progress_current: int = 0
    progress_total: int = 0
    current_module: str | None = None
    overall_score: float | None
    overall_rag: RAGStatus | None
    recommendation: Recommendation | None
    submitted_by: uuid.UUID
    submitted_by_name: str | None = None
    run_started_at: datetime | None = None
    created_at: datetime
    updated_at: datetime
    findings: list[FindingOut] = []
    runs: list[AssessmentRunOut] = []
