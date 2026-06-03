import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Float, ForeignKey, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum
from app.database import Base

class InputType(str, enum.Enum):
    NAME = "name"
    URL = "url"
    REPO = "repo"

class AssessmentStatus(str, enum.Enum):
    PENDING = "pending"
    CONFIRMING = "confirming"
    RUNNING = "running"
    COMPLETE = "complete"
    FAILED = "failed"

class RAGStatus(str, enum.Enum):
    RED = "red"
    AMBER = "amber"
    GREEN = "green"

class Recommendation(str, enum.Enum):
    APPROVE = "approve"
    CONDITIONAL = "conditional"
    REJECT = "reject"

class ReviewMode(str, enum.Enum):
    STANDARD = "standard"
    DEEP_REVIEW = "deep_review"

class Assessment(Base):
    __tablename__ = "assessments"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    product_name: Mapped[str] = mapped_column(String, nullable=False)
    product_url: Mapped[str | None] = mapped_column(String, nullable=True)
    repo_url: Mapped[str | None] = mapped_column(String, nullable=True)
    input_type: Mapped[InputType] = mapped_column(SAEnum(InputType, name="input_type_enum"), nullable=False)
    status: Mapped[AssessmentStatus] = mapped_column(
        SAEnum(AssessmentStatus, name="assessment_status_enum"), default=AssessmentStatus.PENDING
    )
    review_mode: Mapped[ReviewMode] = mapped_column(
        SAEnum(ReviewMode, name="review_mode_enum"), default=ReviewMode.STANDARD
    )
    overall_score: Mapped[float | None] = mapped_column(Float, nullable=True)
    overall_rag: Mapped[RAGStatus | None] = mapped_column(SAEnum(RAGStatus, name="rag_status_enum"), nullable=True)
    recommendation: Mapped[Recommendation | None] = mapped_column(
        SAEnum(Recommendation, name="recommendation_enum"), nullable=True
    )
    submitted_by: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at: Mapped[datetime] = mapped_column(server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(),
        server_onupdate=text("now()"),
    )

    findings: Mapped[list["AssessmentFinding"]] = relationship(back_populates="assessment", lazy="selectin")
    product_confirmation: Mapped["ProductConfirmation | None"] = relationship(
        back_populates="assessment", uselist=False, lazy="selectin"
    )
