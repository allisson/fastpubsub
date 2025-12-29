import pytest
from fastapi.testclient import TestClient

from fastpubsub.api import app
from fastpubsub.database import engine, run_migrations, SessionLocal, Subscription, SubscriptionMessage, Topic


@pytest.fixture(scope="session")
def connection():
    connection = engine.connect()
    run_migrations(command_type="upgrade", revision="head")

    yield connection

    run_migrations(command_type="downgrade", revision="-1")
    connection.close()


@pytest.fixture(scope="function")
def session(connection):
    session = SessionLocal(bind=connection)

    yield session

    session.query(Topic).delete()
    session.query(Subscription).delete()
    session.query(SubscriptionMessage).delete()
    session.commit()
    session.close()


@pytest.fixture
def client():
    return TestClient(app)
