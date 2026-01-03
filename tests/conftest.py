"""Test configuration and fixtures for fastpubsub application tests."""

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
    """Create an async engine for testing.

    Sets up a test database with migrations applied for the test session.
    Tears down the database after all tests complete.

    Yields:
        Async SQLAlchemy engine configured for testing.
    """
    await run_migrations(command_type="upgrade", revision="head")
    yield engine
    await run_migrations(command_type="downgrade", revision="-1")
    await engine.dispose()


@pytest_asyncio.fixture(scope="function")
async def session(async_engine):
    """Create a database session for each test function.

    Provides a clean database session that automatically cleans up
    all test data after each test function completes.

    Args:
        async_engine: The async database engine fixture.

    Yields:
        Async database session for test operations.
    """
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
    """Create a test client for FastAPI application.

    Returns:
        TestClient configured for testing the FastAPI application.
    """
    return TestClient(app)
