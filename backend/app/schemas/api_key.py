import uuid
from datetime import datetime
from pydantic import BaseModel


class APIKeyCreate(BaseModel):
    name: str
    expires_in_days: int  # 1, 7, 30, 90, 180, 365


class APIKeyOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    name: str
    key_prefix: str
    expires_at: datetime
    created_at: datetime
    last_used_at: datetime | None
    is_active: bool


class APIKeyCreated(APIKeyOut):
    key: str  # plaintext, returned once only
