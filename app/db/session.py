from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import text
from app.core.config import settings


engine = create_async_engine(
    settings.DB_URL,
    echo=False,  # True solo en desarrollo
    pool_pre_ping=True,
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)

if __name__ == "__main__":
    import asyncio

    async def test_connection():
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            print(result.scalar())

    asyncio.run(test_connection())
