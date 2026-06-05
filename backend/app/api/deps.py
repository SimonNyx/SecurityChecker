import hashlib
import uuid
from datetime import datetime
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.core.security import decode_access_token
from app.models.user import User
from app.models.api_key import APIKey

bearer = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(bearer),
    db: AsyncSession = Depends(get_db),
) -> User:
    token = credentials.credentials

    # API key path: sk_ prefix
    if token.startswith("sk_"):
        key_hash = hashlib.sha256(token.encode()).hexdigest()
        result = await db.execute(
            select(APIKey).where(
                APIKey.key_hash == key_hash,
                APIKey.is_active == True,
                APIKey.expires_at > datetime.utcnow(),
            )
        )
        api_key = result.scalar_one_or_none()
        if not api_key:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired API key")
        # Update last_used_at
        api_key.last_used_at = datetime.utcnow()
        await db.commit()
        user_result = await db.execute(select(User).where(User.id == api_key.user_id, User.is_active == True))
        user = user_result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
        return user

    # JWT path
    try:
        payload = decode_access_token(token)
        if payload.get("type") != "access":
            raise JWTError("Not an access token")
        user_id = payload.get("sub")
        if not user_id:
            raise JWTError("Missing sub claim")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id), User.is_active == True))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")
    return user
