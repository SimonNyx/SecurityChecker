import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User, Role
from app.schemas.user import UserCreate, UserUpdate, UserOut
from app.core.security import hash_password
from app.core.rbac import require_role
from app.core.audit import log_action

router = APIRouter(prefix="/users", tags=["users"])

@router.get("", response_model=list[UserOut])
async def list_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(User).order_by(User.created_at))
    return result.scalars().all()

@router.post("", response_model=UserOut, status_code=status.HTTP_201_CREATED)
async def create_user(
    body: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    existing = await db.execute(select(User).where(User.email == body.email))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail="Email already registered")
    user = User(
        email=body.email,
        hashed_password=hash_password(body.password),
        full_name=body.full_name,
        role=body.role,
        can_generate_api_keys=(body.role == Role.ADMIN),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    await log_action(db, current_user.id, "create_user", "user", user.id)
    await db.commit()
    return user

@router.patch("/{user_id}", response_model=UserOut)
@router.put("/{user_id}", response_model=UserOut)
async def update_user(
    user_id: uuid.UUID,
    body: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    if body.full_name is not None:
        user.full_name = body.full_name
    if body.role is not None:
        user.role = body.role
    if body.is_active is not None:
        user.is_active = body.is_active
    if body.can_generate_api_keys is not None:
        user.can_generate_api_keys = body.can_generate_api_keys
    await db.commit()
    await db.refresh(user)
    await log_action(db, current_user.id, "update_user", "user", user_id)
    await db.commit()
    return user
