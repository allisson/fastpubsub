import asyncio

import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient
from sqlalchemy import delete

from fastpubsub.api import app
from fastpubsub.database import engine, run_migrations, SessionLocal, Subscription, SubscriptionMessage, Topic


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def async_engine():
    """Create an async engine for testing."""
    await run_migrations(command_type="upgrade", revision="head")
    yield engine
    await run_migrations(command_type="downgrade", revision="-1")
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(async_engine):
    async with SessionLocal() as sess:
        yield sess
        # Clean up after each test
        await sess.execute(delete(SubscriptionMessage))
        await sess.execute(delete(Subscription))
        await sess.execute(delete(Topic))
        await sess.commit()


@pytest.fixture
def client():
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
