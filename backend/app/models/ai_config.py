import uuid
import enum
from sqlalchemy import String, Boolean
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Enum as SAEnum
from app.database import Base

class AIProvider(str, enum.Enum):
    OPENWEBUI = "openwebui"
    OLLAMA = "ollama"
    GEMINI = "gemini"

class AIProviderConfig(Base):
    __tablename__ = "ai_provider_config"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    provider: Mapped[AIProvider] = mapped_column(SAEnum(AIProvider, name="ai_provider_enum"), nullable=False)
    base_url: Mapped[str] = mapped_column(String, nullable=False)
    api_key: Mapped[str] = mapped_column(String, nullable=False, default="")
    model_name: Mapped[str] = mapped_column(String, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=False)
