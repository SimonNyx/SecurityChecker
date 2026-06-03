import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.main import app
from app.database import Base, get_db
from app.models.user import User, Role
from app.core.security import hash_password

TEST_DB_URL = "postgresql+asyncpg://securitychecker:changeme@localhost:5432/securitychecker_test"

# Schema is created once per process using a module-level flag
_schema_created = False

@pytest_asyncio.fixture
async def db():
    global _schema_created
    engine = create_async_engine(TEST_DB_URL)
    if not _schema_created:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
            await conn.run_sync(Base.metadata.create_all)
        _schema_created = True

    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
        await session.rollback()
        # Truncate all tables to isolate tests
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(text(f"TRUNCATE TABLE {table.name} RESTART IDENTITY CASCADE"))
        await session.commit()

    await engine.dispose()

@pytest_asyncio.fixture
async def client(db):
    async def override_db():
        yield db
    app.dependency_overrides[get_db] = override_db
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        yield c
    app.dependency_overrides.clear()

async def _make_user(db, email, role, password="password123"):
    user = User(email=email, hashed_password=hash_password(password), full_name="Test User", role=role)
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@pytest_asyncio.fixture
async def admin_user(db):
    return await _make_user(db, "admin@test.com", Role.ADMIN)

@pytest_asyncio.fixture
async def analyst_user(db):
    return await _make_user(db, "analyst@test.com", Role.ANALYST)

@pytest_asyncio.fixture
async def viewer_user(db):
    return await _make_user(db, "viewer@test.com", Role.VIEWER)

async def login(client, email, password="password123"):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]
