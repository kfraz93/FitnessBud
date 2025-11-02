import datetime
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import text, DateTime, pool

# Import application settings from the core layer
from core.config import settings


# 1. Base Class for ORM Models

class Base(DeclarativeBase):
    """
    Base class for all SQLAlchemy ORM models. This provides common fields
    like ID and timestamps to all our database tables.
    """
    __abstract__ = True

    # Common primary key with index
    id: Mapped[int] = mapped_column(primary_key=True, index=True)

    # Timestamps (managed by the database)
    created_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP")
    )
    updated_at: Mapped[datetime.datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=text("CURRENT_TIMESTAMP"),
        onupdate=datetime.datetime.now
    )


# 2. Database Engine and Session Factory (The Persistence Adapter)

# Create the asynchronous engine using the configured URL.
# The poolclass is set to NullPool for better performance with async drivers.
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    poolclass=pool.NullPool,
)

# Configure the session maker for local, async sessions
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


# 3. FastAPI Dependency Function

async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency that yields a database session and ensures it is closed
    regardless of success or failure.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # If an exception occurs, ensure any pending changes are rolled back
            await session.rollback()
            raise
        finally:
            await session.close()


async def create_db_and_tables():
    """
    Creates all tables defined in Base.metadata.
    This is the simple, non-Alembic way to initialize the database.
    """
    async with engine.begin() as conn:
        # We must import the models here so that the Base class
        # "discovers" them before we call create_all()
        from infrastructure import models

        # This command tells SQLAlchemy to create all tables
        # that inherit from our 'Base' class.
        await conn.run_sync(Base.metadata.create_all)