import uuid
from datetime import datetime
from sqlalchemy import String, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.database import Base

class ProductConfirmation(Base):
    __tablename__ = "product_confirmations"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    assessment_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("assessments.id"), nullable=False)
    ai_suggested_name: Mapped[str] = mapped_column(String, nullable=False)
    ai_suggested_vendor: Mapped[str] = mapped_column(String, nullable=False)
    ai_suggested_url: Mapped[str] = mapped_column(String, nullable=False)
    confirmed_by: Mapped[uuid.UUID | None] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=True)
    confirmed_at: Mapped[datetime | None] = mapped_column(nullable=True)

    assessment: Mapped["Assessment"] = relationship(back_populates="product_confirmation")
