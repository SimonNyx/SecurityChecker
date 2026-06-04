"""Run with: cd backend && python scripts/seed.py"""
import asyncio
import secrets
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.database import Base
from app.models.user import User, Role
from app.models.ai_config import AIProviderConfig, AIProvider
from app.core.security import hash_password

async def seed():
    from sqlalchemy import select
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        # Admin user — skip if already exists
        existing = await db.execute(select(User).where(User.email == "admin@securitychecker.local"))
        if not existing.scalar_one_or_none():
            password = secrets.token_urlsafe(16)
            admin = User(
                email="admin@securitychecker.local",
                hashed_password=hash_password(password),
                full_name="Admin",
                role=Role.ADMIN,
            )
            db.add(admin)
            print(f"Seeded: admin@securitychecker.local / {password}")
            print("IMPORTANT: Save this password — it will not be shown again.")
        else:
            print("Skipped: admin user already exists")

        # AI config — skip if already exists
        existing_cfg = await db.execute(select(AIProviderConfig).where(AIProviderConfig.is_active == True))
        if not existing_cfg.scalar_one_or_none():
            config = AIProviderConfig(
                provider=AIProvider.OPENWEBUI,
                base_url=settings.openwebui_base_url,
                api_key="",
                model_name="llama3",
                is_active=True,
            )
            db.add(config)
            print(f"Seeded: OpenWebUI config → {settings.openwebui_base_url}")
        else:
            print("Skipped: AI config already exists")

        await db.commit()

asyncio.run(seed())
