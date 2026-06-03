import uuid
import enum
from datetime import datetime
from sqlalchemy import String, Float, Text, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy import Enum as SAEnum
from app.database import Base
from app.models.assessment import RAGStatus

class Category(str, enum.Enum):
    VENDOR_TRUST = "vendor_trust"
    CVE = "cve"
    MAINTENANCE = "maintenance"
    DEPENDENCY = "dependency"
    ENCRYPTION = "encryption"
    LOGGING = "logging"
    DATA_EXFILTRATION = "data_exfiltration"
    THIRD_PARTY = "third_party"

class AssessmentFinding(Base):
    __tablename__ = "assessment_findings"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    category: Mapped[Category] = mapped_column(SAEnum(Category, name="category_enum"), nullable=False)
    score: Mapped[float] = mapped_column(Float, nullable=False)
    rag: Mapped[RAGStatus] = mapped_column(SAEnum(RAGStatus, name="rag_status_enum"), nullable=False)
    summary: Mapped[str] = mapped_column(Text, nullable=False)
    detail: Mapped[dict] = mapped_column(JSONB, nullable=False, default=dict)
    analyst_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    edited_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    edited_at: Mapped[datetime | None] = mapped_column(nullable=True)

    assessment: Mapped["Assessment"] = relationship(back_populates="findings")
