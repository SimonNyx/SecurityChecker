import uuid
from datetime import datetime
from pydantic import BaseModel
from app.models.finding import Category
from app.models.assessment import RAGStatus

class FindingOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    assessment_id: uuid.UUID
    category: Category
    score: float
    rag: RAGStatus
    summary: str
    detail: dict
    analyst_notes: str | None
    edited_by: uuid.UUID | None
    edited_at: datetime | None

class FindingUpdate(BaseModel):
    analyst_notes: str | None = None
    score: float | None = None
