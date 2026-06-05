import hashlib
import secrets
import uuid
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models.user import User
from app.models.api_key import APIKey
from app.schemas.api_key import APIKeyCreate, APIKeyOut, APIKeyCreated
from app.api.deps import get_current_user

router = APIRouter(prefix="/auth/api-keys", tags=["api-keys"])

ALLOWED_EXPIRY_DAYS = {1, 7, 30, 90, 180, 365}


@router.get("", response_model=list[APIKeyOut])
async def list_api_keys(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(APIKey).where(APIKey.user_id == current_user.id).order_by(APIKey.created_at.desc())
    )
    return result.scalars().all()


@router.post("", response_model=APIKeyCreated, status_code=status.HTTP_201_CREATED)
async def create_api_key(
    body: APIKeyCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    if not current_user.can_generate_api_keys:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="API key generation not permitted for this account")
    if body.expires_in_days not in ALLOWED_EXPIRY_DAYS:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"expires_in_days must be one of {sorted(ALLOWED_EXPIRY_DAYS)}")

    raw_key = "sk_" + secrets.token_urlsafe(40)
    key_hash = hashlib.sha256(raw_key.encode()).hexdigest()
    key_prefix = raw_key[3:15]  # 12 chars after sk_ for display

    api_key = APIKey(
        user_id=current_user.id,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        expires_at=datetime.utcnow() + timedelta(days=body.expires_in_days),
    )
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return APIKeyCreated(
        id=api_key.id,
        name=api_key.name,
        key_prefix=api_key.key_prefix,
        expires_at=api_key.expires_at,
        created_at=api_key.created_at,
        last_used_at=api_key.last_used_at,
        is_active=api_key.is_active,
        key=raw_key,
    )


@router.delete("/{key_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_api_key(
    key_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(APIKey).where(APIKey.id == key_id, APIKey.user_id == current_user.id)
    )
    api_key = result.scalar_one_or_none()
    if not api_key:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="API key not found")
    api_key.is_active = False
    await db.commit()
