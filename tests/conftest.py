import pytest
import asyncio
from typing import AsyncGenerator
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.pool import StaticPool
from dotenv import load_dotenv

# --- Local Imports ---
from api.main import app
from core.config import settings
from infrastructure.db import Base, get_db_session
from domain.auth import auth_service
from infrastructure.orm_models import User

load_dotenv(dotenv_path='./.env.test', override=True)

@pytest.fixture(scope="session")
def mock_settings():
    return settings

# --- 2. Test Database Setup ---
TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"

engine = create_async_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

TestingSessionLocal = async_sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False
)

# --- 3. Dependency Overrides ---
async def override_get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with TestingSessionLocal() as session:
        yield session

app.dependency_overrides[get_db_session] = override_get_db_session

# --- 4. Testing Lifecycle Fixtures ---

@pytest.fixture(scope="session")
def event_loop():
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(autouse=True)
async def setup_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

# --- 5. Client & Auth Fixtures ---

@pytest.fixture
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac

@pytest.fixture
async def test_user(setup_db):
    async with TestingSessionLocal() as session:
        hashed = auth_service.hash_password("password123")
        user = User(
            email="test@example.com",
            hashed_password=hashed,
            age=30,
            goal="gain_muscle",
            equipment="full_gym",
            is_active=True
        )
        session.add(user)
        await session.commit()
        await session.refresh(user)
        return user

@pytest.fixture
async def authenticated_client(client, test_user) -> AsyncClient:
    token_response = auth_service.get_auth_tokens(user_id=test_user.id)
    token = token_response.access_token
    client.headers.update({"Authorization": f"Bearer {token}"})
    return client