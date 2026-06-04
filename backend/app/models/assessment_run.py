import uuid
from datetime import datetime
from sqlalchemy import String, Float, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum
from app.database import Base
from app.models.assessment import RAGStatus, Recommendation, ReviewMode


class AssessmentRun(Base):
    __tablename__ = "assessment_runs"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id", ondelete="CASCADE"), nullable=False)
    run_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    run_at: Mapped[datetime] = mapped_column(server_default=func.now())
    review_mode: Mapped[ReviewMode] = mapped_column(SAEnum(ReviewMode, name="review_mode_enum"), nullable=False)
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_rag: Mapped[RAGStatus | None] = mapped_column(SAEnum(RAGStatus, name="rag_status_enum"), nullable=True)
    recommendation: Mapped[Recommendation | None] = mapped_column(SAEnum(Recommendation, name="recommendation_enum"), nullable=True)

    runner: Mapped["User"] = relationship(foreign_keys=[run_by], lazy="selectin")

    @property
    def run_by_name(self) -> str | None:
        return self.runner.full_name if self.runner else None
