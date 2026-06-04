import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.assessment import InputType, AssessmentStatus, RAGStatus, Recommendation, ReviewMode
from app.schemas.finding import FindingOut

class AssessmentCreate(BaseModel):
    product_name: str
    product_url: str | None = None
    repo_url: str | None = None
    review_mode: ReviewMode = ReviewMode.STANDARD

class ProductConfirmRequest(BaseModel):
    confirmed_name: str
    confirmed_vendor: str
    confirmed_url: str

class RerunRequest(BaseModel):
    review_mode: ReviewMode

class AssessmentOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    product_name: str
    product_url: str | None
    repo_url: str | None
    input_type: InputType
    status: AssessmentStatus
    review_mode: ReviewMode
    overall_score: float | None
    overall_rag: RAGStatus | None
    recommendation: Recommendation | None
    submitted_by: uuid.UUID
    created_at: datetime
    updated_at: datetime
    findings: list[FindingOut] = []
