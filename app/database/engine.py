from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from .models import Base

# Database URL for SQLite
DATABASE_URL = "sqlite+aiosqlite:///./telegram_bot_memory.db"

# Create async engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,  # Set to False in production
    future=True
)

# Create async session maker
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False
)


async def create_tables():
    """Create all tables in the database"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_session():
    """Dependency to get database session"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close() 