"""Database models and utilities for fastpubsub application."""

from pathlib import Path

import sqlalchemy as sa
from alembic.config import command, Config
from sqlalchemy import inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from fastpubsub.config import settings
from fastpubsub.logger import get_logger

logger = get_logger(__name__)
engine = create_async_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=settings.database_pool_pre_ping,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)
SessionLocal = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class Base(DeclarativeBase):
    """Base declarative class for all database models.

    Provides common functionality for all ORM models in the application.
    """

    def to_dict(self):
        """Convert model instance to dictionary.

        Returns:
            Dictionary mapping column names to their values.
        """
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Topic(Base):
    """Database model representing a topic in the pub/sub system.

    Topics are used to organize messages and subscriptions.
    """

    id = sa.Column(sa.Text, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    __tablename__ = "topics"

    def __repr__(self):
        return f"Topic(id={self.id})"


class Subscription(Base):
    """Database model representing a subscription to a topic.

    Subscriptions define how messages from a topic should be consumed,
    including filtering, delivery attempts, and backoff configuration.
    """

    id = sa.Column(sa.Text, primary_key=True)
    topic_id = sa.Column(sa.Text, nullable=False)
    filter = sa.Column(postgresql.JSONB, nullable=False, default={})
    max_delivery_attempts = sa.Column(sa.Integer, nullable=False)
    backoff_min_seconds = sa.Column(sa.Integer, nullable=False)
    backoff_max_seconds = sa.Column(sa.Integer, nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    __tablename__ = "subscriptions"

    def __repr__(self):
        return f"Subscription(id={self.id}, topic_id={self.topic_id})"


class SubscriptionMessage(Base):
    """Database model representing a message in a subscription's queue.

    Tracks message delivery status, attempts, and processing state.
    """

    id = sa.Column(postgresql.UUID, primary_key=True)
    subscription_id = sa.Column(sa.Text, nullable=False)
    payload = sa.Column(postgresql.JSONB, nullable=False)
    status = sa.Column(sa.Text, nullable=False)
    delivery_attempts = sa.Column(sa.Integer, nullable=False)
    available_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    locked_at = sa.Column(sa.DateTime(timezone=True), nullable=True)
    locked_by = sa.Column(sa.Text, nullable=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    acked_at = sa.Column(sa.DateTime(timezone=True), nullable=True)

    __tablename__ = "subscription_messages"

    def __repr__(self):
        return f"SubscriptionMessage(id={self.id}, subscription_id={self.subscription_id})"


class Client(Base):
    """Database model representing an authorized client of the pub/sub system.

    Clients can be granted scopes to perform specific operations.
    """

    id = sa.Column(postgresql.UUID, primary_key=True)
    name = sa.Column(sa.Text, nullable=False)
    scopes = sa.Column(sa.Text, nullable=False)
    is_active = sa.Column(sa.Boolean, nullable=False)
    secret_hash = sa.Column(sa.Text, nullable=False)
    token_version = sa.Column(sa.Integer, nullable=False)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)
    updated_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    __tablename__ = "clients"

    def __repr__(self):
        return f"Client(id={self.id}, name={self.name})"


async def run_migrations(command_type: str = "upgrade", revision: str = "head") -> None:
    """Run database migrations using Alembic.

    Executes database schema migrations to update or revert the database structure.

    Args:
        command_type: Migration command to execute ('upgrade' or 'downgrade').
        revision: Alembic revision to apply ('head' for latest, specific revision ID, etc.).

    Raises:
        Exception: If migration command fails.
    """
    parent_path = Path(__file__).parents[1]
    script_location = parent_path.joinpath(Path("migrations"))
    ini_location = parent_path.joinpath(Path("alembic.ini"))
    logger.info(
        "running db migrations",
        extra=dict(ini_location=ini_location, script_location=script_location),
    )
    # Use the database URL as-is for Alembic
    # psycopg works fine with Alembic in synchronous mode
    alembic_cfg = Config(ini_location)
    alembic_cfg.set_main_option("script_location", str(script_location))
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

    match command_type:
        case "upgrade":
            command.upgrade(alembic_cfg, revision)
        case "downgrade":
            command.downgrade(alembic_cfg, revision)

    logger.info(
        "finished db migrations",
        extra=dict(ini_location=ini_location, script_location=script_location),
    )


def is_unique_violation(exc: IntegrityError) -> bool:
    """Check if an IntegrityError is a unique constraint violation.

    Args:
        exc: The IntegrityError exception to check.

    Returns:
        True if the exception is a unique constraint violation, False otherwise.
    """
    return "psycopg.errors.UniqueViolation" in exc.args[0]


def is_foreign_key_violation(exc: IntegrityError) -> bool:
    """Check if an IntegrityError is a foreign key constraint violation.

    Args:
        exc: The IntegrityError exception to check.

    Returns:
        True if the exception is a foreign key constraint violation, False otherwise.
    """
    return "psycopg.errors.ForeignKeyViolation" in exc.args[0]
