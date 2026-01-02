import pytest
import pytest_asyncio
from fastapi.testclient import TestClient
from sqlalchemy import delete

from fastpubsub.api import app
from fastpubsub.database import (
    Client,
    engine,
    run_migrations,
    SessionLocal,
    Subscription,
    SubscriptionMessage,
    Topic,
)


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
        await sess.execute(delete(Client))
        await sess.commit()


@pytest.fixture
def client():
    return TestClient(app)
