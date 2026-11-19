from unittest.mock import AsyncMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401 — registers all models with Base before table creation
from app.database import Base, get_session
from app.main import app

TEST_DATABASE_URL = "sqlite+aiosqlite:///:memory:"


@pytest.fixture
async def engine():
    # StaticPool reuses a single connection so all sessions share the same
    # in-memory SQLite database within a test.
    _engine = create_async_engine(TEST_DATABASE_URL, poolclass=StaticPool)
    async with _engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield _engine
    await _engine.dispose()


@pytest.fixture
async def session(engine):
    _factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with _factory() as s:
        yield s


@pytest.fixture
async def client(engine):
    """HTTP test client wired to an isolated in-memory database.

    Overrides the get_session dependency so every request uses the test engine.
    Patches create_tables so the lifespan does not touch the real database.
    """
    _factory = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async def _override_get_session():
        async with _factory() as s:
            yield s

    app.dependency_overrides[get_session] = _override_get_session
    with patch("app.main.create_tables", new_callable=AsyncMock):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
            yield c
    app.dependency_overrides.clear()
