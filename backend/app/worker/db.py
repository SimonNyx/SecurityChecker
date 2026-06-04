import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings


@asynccontextmanager
async def worker_db():
    # Create engine fresh per call — Celery forks workers with new event loops,
    # so a module-level engine would be attached to the wrong loop.
    engine = create_async_engine(settings.database_url)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    try:
        async with session_factory() as session:
            yield session
            await session.commit()
    finally:
        await engine.dispose()


def run_async(coro):
    """Run an async coroutine from a sync Celery task."""
    return asyncio.run(coro)
