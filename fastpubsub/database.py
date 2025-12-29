from pathlib import Path

import sqlalchemy as sa
from alembic.config import command, Config
from sqlalchemy import create_engine, inspect
from sqlalchemy.dialects import postgresql
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from fastpubsub.config import settings
from fastpubsub.logger import get_logger

logger = get_logger(__name__)
engine = create_engine(
    settings.database_url,
    echo=settings.database_echo,
    pool_pre_ping=settings.database_pool_pre_ping,
    pool_size=settings.database_pool_size,
    max_overflow=settings.database_max_overflow,
)
SessionLocal = sessionmaker(bind=engine)


class Base(DeclarativeBase):
    def to_dict(self):
        return {c.key: getattr(self, c.key) for c in inspect(self).mapper.column_attrs}


class Topic(Base):
    id = sa.Column(sa.Text, primary_key=True)
    created_at = sa.Column(sa.DateTime(timezone=True), nullable=False)

    __tablename__ = "topics"

    def __repr__(self):
        return f"Topic(id={self.id})"


class Subscription(Base):
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
    id = sa.Column(sa.BigInteger, primary_key=True)
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


def run_migrations(command_type: str = "upgrade", revision: str = "head") -> None:
    parent_path = Path(__file__).parents[1]
    script_location = parent_path.joinpath(Path("migrations"))
    ini_location = parent_path.joinpath(Path("alembic.ini"))
    logger.info(
        "running db migrations",
        extra=dict(ini_location=ini_location, script_location=script_location),
    )
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
    return "psycopg.errors.UniqueViolation" in exc.args[0]


def is_foreign_key_violation(exc: IntegrityError) -> bool:
    return "psycopg.errors.ForeignKeyViolation" in exc.args[0]
