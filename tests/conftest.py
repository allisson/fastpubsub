import asyncio
import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from fastpubsub.api import app
from fastpubsub.database import engine, run_migrations, SessionLocal, Subscription, SubscriptionMessage, Topic


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest_asyncio.fixture(scope="session")
async def connection():
    async with engine.connect() as conn:
        await run_migrations(command_type="upgrade", revision="head")
        yield conn
        await run_migrations(command_type="downgrade", revision="-1")


@pytest_asyncio.fixture(scope="function")
async def session(connection):
    async with SessionLocal() as sess:
        yield sess
        # Clean up after each test
        await sess.execute(Topic.__table__.delete())
        await sess.execute(Subscription.__table__.delete())
        await sess.execute(SubscriptionMessage.__table__.delete())
        await sess.commit()


@pytest.fixture
def client():
    return TestClient(app)


@pytest_asyncio.fixture
async def async_client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
