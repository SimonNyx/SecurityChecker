import asyncio
from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from app.config import settings

_engine = create_async_engine(settings.database_url)
_Session = async_sessionmaker(_engine, expire_on_commit=False)

@asynccontextmanager
async def worker_db():
    async with _Session() as session:
        yield session
        await session.commit()

def run_async(coro):
    """Run an async coroutine from sync Celery task code."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                future = pool.submit(asyncio.run, coro)
                return future.result()
    except RuntimeError:
        pass
    return asyncio.run(coro)
