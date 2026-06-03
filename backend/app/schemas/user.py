import uuid
from datetime import datetime
from pydantic import BaseModel, EmailStr
from app.models.user import Role

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: Role = Role.VIEWER

class UserUpdate(BaseModel):
    full_name: str | None = None
    role: Role | None = None
    is_active: bool | None = None

class UserOut(BaseModel):
    model_config = {"from_attributes": True}
    id: uuid.UUID
    email: str
    full_name: str
    role: Role
    is_active: bool
    created_at: datetime
