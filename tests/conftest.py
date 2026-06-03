import asyncio
import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from app.main import app
from app.database import Base, get_db
from app.models.user import User, Role
from app.core.security import hash_password

TEST_DB_URL = "postgresql+asyncpg://securitychecker:changeme@localhost:5432/securitychecker_test"

test_engine = create_async_engine(TEST_DB_URL)
TestSession = async_sessionmaker(test_engine, expire_on_commit=False)

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def db(setup_db):
    async with TestSession() as session:
        yield session
        await session.rollback()

@pytest_asyncio.fixture(scope="session", loop_scope="session")
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

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def admin_user(db):
    return await _make_user(db, "admin@test.com", Role.ADMIN)

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def analyst_user(db):
    return await _make_user(db, "analyst@test.com", Role.ANALYST)

@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def viewer_user(db):
    return await _make_user(db, "viewer@test.com", Role.VIEWER)

async def login(client, email, password="password123"):
    r = await client.post("/api/v1/auth/login", json={"email": email, "password": password})
    return r.json()["access_token"]
