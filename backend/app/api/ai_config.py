from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.config import settings
from app.models.user import User, Role
from app.models.ai_config import AIProviderConfig
from app.schemas.ai_config import AIConfigOut, AIConfigUpdate
from app.core.rbac import require_role
from app.core.audit import log_action
from app.worker.ai_client import AIClient

router = APIRouter(prefix="/ai-config", tags=["ai-config"])

def _encrypt(value: str) -> str:
    if not value:
        return ""
    f = Fernet(settings.encryption_key.encode())
    return f.encrypt(value.encode()).decode()

@router.get("", response_model=AIConfigOut)
async def get_ai_config(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.is_active == True))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="No active AI provider configured")
    return config

@router.put("", response_model=AIConfigOut)
async def update_ai_config(
    body: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.is_active == True))
    config = result.scalar_one_or_none()
    if not config:
        config = AIProviderConfig(is_active=True)
        db.add(config)

    if body.provider is not None:
        config.provider = body.provider
    if body.base_url is not None:
        config.base_url = body.base_url
    if body.api_key is not None:
        config.api_key = _encrypt(body.api_key)
    if body.model_name is not None:
        config.model_name = body.model_name

    await db.commit()
    await db.refresh(config)
    await log_action(db, current_user.id, "update_ai_config", "ai_config", config.id)
    await db.commit()
    return config


@router.post("/test")
async def test_ai_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    """Test connectivity to the currently configured AI provider."""
    result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.is_active == True))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail="No active AI provider configured")

    api_key = ""
    if config.api_key:
        f = Fernet(settings.encryption_key.encode())
        api_key = f.decrypt(config.api_key.encode()).decode()

    client = AIClient({
        "provider": config.provider,
        "base_url": config.base_url,
        "api_key": api_key,
        "model_name": config.model_name,
    })
    result = await client.test_connection()
    if not result["ok"]:
        raise HTTPException(status_code=502, detail=result["error"])
    return {"ok": True, "provider": config.provider.value, "model": config.model_name, "response": result["response"]}
