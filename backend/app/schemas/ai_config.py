import uuid
from pydantic import BaseModel
from app.models.ai_config import AIProvider

class AIConfigOut(BaseModel):
    model_config = {"from_attributes": True, "protected_namespaces": ()}
    id: uuid.UUID
    provider: AIProvider
    base_url: str
    model_name: str
    is_active: bool
    has_api_key: bool = False

    @classmethod
    def from_orm_with_key_flag(cls, obj) -> "AIConfigOut":
        return cls(
            id=obj.id,
            provider=obj.provider,
            base_url=obj.base_url,
            model_name=obj.model_name,
            is_active=obj.is_active,
            has_api_key=bool(obj.api_key),
        )

class AIConfigUpdate(BaseModel):
    model_config = {"protected_namespaces": ()}
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
