from cryptography.fernet import Fernet
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.config import settings
from app.models.user import User, Role
from app.models.ai_config import AIProviderConfig, AIProvider
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


def _all_providers_response(configs: list[AIProviderConfig]) -> list[AIConfigOut]:
    existing = {c.provider: c for c in configs}
    result = []
    for provider in AIProvider:
        if provider in existing:
            result.append(AIConfigOut.from_orm_with_key_flag(existing[provider]))
        else:
            result.append(AIConfigOut(
                id=__import__('uuid').uuid4(),
                provider=provider,
                base_url="",
                model_name="",
                is_active=False,
                has_api_key=False,
            ))
    return result


@router.get("", response_model=list[AIConfigOut])
async def list_ai_configs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(AIProviderConfig))
    return _all_providers_response(result.scalars().all())


@router.put("/{provider}", response_model=AIConfigOut)
async def upsert_ai_config(
    provider: AIProvider,
    body: AIConfigUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.provider == provider))
    config = result.scalar_one_or_none()
    if not config:
        config = AIProviderConfig(provider=provider, is_active=False)
        db.add(config)

    if body.base_url is not None:
        config.base_url = body.base_url
    if body.model_name is not None:
        config.model_name = body.model_name
    if body.api_key is not None:
        config.api_key = _encrypt(body.api_key)

    await db.commit()
    await db.refresh(config)
    await log_action(db, current_user.id, "update_ai_config", "ai_config", config.id,
                     {"provider": provider.value})
    await db.commit()
    return AIConfigOut.from_orm_with_key_flag(config)


@router.post("/{provider}/activate", response_model=AIConfigOut)
async def activate_ai_config(
    provider: AIProvider,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
    result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.provider == provider))
    config = result.scalar_one_or_none()
    if not config:
        raise HTTPException(status_code=404, detail=f"No config saved for {provider.value} yet")
    if not config.base_url or not config.model_name:
        raise HTTPException(status_code=400, detail="Save base URL and model name before activating")

    # Deactivate all others
    all_result = await db.execute(select(AIProviderConfig).where(AIProviderConfig.is_active == True))
    for other in all_result.scalars().all():
        other.is_active = False

    config.is_active = True
    await db.commit()
    await db.refresh(config)
    await log_action(db, current_user.id, "activate_ai_config", "ai_config", config.id,
                     {"provider": provider.value})
    await db.commit()
    return AIConfigOut.from_orm_with_key_flag(config)


@router.post("/test")
async def test_ai_connection(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(Role.ADMIN)),
):
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
    test_result = await client.test_connection()
    if not test_result["ok"]:
        raise HTTPException(status_code=502, detail="AI provider connection failed")
    return {"ok": True, "provider": config.provider.value, "model": config.model_name, "response": test_result["response"]}
