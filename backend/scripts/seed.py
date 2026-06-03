"""Run with: cd backend && python scripts/seed.py"""
import asyncio
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings
from app.database import Base
from app.models.user import User, Role
from app.models.ai_config import AIProviderConfig, AIProvider
from app.core.security import hash_password

async def seed():
    engine = create_async_engine(settings.database_url)
    Session = async_sessionmaker(engine, expire_on_commit=False)

    async with Session() as db:
        admin = User(
            email="admin@securitychecker.local",
            hashed_password=hash_password("changeme"),
            full_name="Admin",
            role=Role.ADMIN,
        )
        config = AIProviderConfig(
            provider=AIProvider.OPENWEBUI,
            base_url=settings.openwebui_base_url,
            api_key="",
            model_name="llama3",
            is_active=True,
        )
        db.add(admin)
        db.add(config)
        await db.commit()
        print("Seeded: admin@securitychecker.local / changeme")
        print(f"Seeded: OpenWebUI config → {settings.openwebui_base_url}")

asyncio.run(seed())
