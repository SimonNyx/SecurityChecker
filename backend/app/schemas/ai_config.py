import uuid
from pydantic import BaseModel
from app.models.ai_config import AIProvider

class AIConfigOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    provider: AIProvider
    base_url: str
    model_name: str
    is_active: bool

class AIConfigUpdate(BaseModel):
    provider: AIProvider | None = None
    base_url: str | None = None
    api_key: str | None = None
    model_name: str | None = None
    is_active: bool | None = None
