import datetime
import uuid
from typing import Any

from psycopg.types.json import Json
from sqlalchemy import select, text
from sqlalchemy.exc import IntegrityError

from fastpubsub.database import (
    is_foreign_key_violation,
    is_unique_violation,
    SessionLocal,
)
from fastpubsub.database import Subscription as DBSubscription
from fastpubsub.database import (
    Topic as DBTopic,
)
from fastpubsub.exceptions import AlreadyExistsError, NotFoundError
from fastpubsub.models import (
    CreateSubscription,
    CreateTopic,
    Message,
    Subscription,
    SubscriptionMetrics,
    Topic,
)


def utc_now():
    return datetime.datetime.now(datetime.UTC)


async def _get_entity(session, model, entity_id: str, error_message: str):
    """Generic helper to get an entity by ID or raise NotFoundError."""
    stmt = select(model).filter_by(id=entity_id)
    result = await session.execute(stmt)
    entity = result.scalar_one_or_none()
    if entity is None:
        raise NotFoundError(error_message) from None
    return entity


async def _delete_entity(session, model, entity_id: str, error_message: str) -> None:
    """Generic helper to delete an entity by ID or raise NotFoundError."""
    entity = await _get_entity(session, model, entity_id, error_message)
    session.delete(entity)
    await session.commit()


async def _execute_sql_command(query: str, params: dict) -> bool:
    """Generic helper to execute SQL commands.

    Executes a SQL command and returns True if exactly one row was affected.
    This is appropriate for commands that are expected to affect a single row,
    such as message acknowledgment operations. Commands that may legitimately
    affect 0 or multiple rows should handle the return value accordingly.

    Args:
        query: SQL query to execute
        params: Query parameters

    Returns:
        True if exactly one row was affected, False otherwise
    """
    stmt = text(query)
    async with SessionLocal() as session:
        result = await session.execute(stmt, params)
        rowcount = result.rowcount
        await session.commit()
    return rowcount == 1


async def create_topic(data: CreateTopic) -> Topic:
    async with SessionLocal() as session:
        db_topic = DBTopic(id=data.id, created_at=utc_now())
        session.add(db_topic)

        try:
            await session.commit()
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise AlreadyExistsError("This topic already exists") from None
            raise

        return Topic(**db_topic.to_dict())


async def get_topic(topic_id: str) -> Topic:
    async with SessionLocal() as session:
        db_topic = await _get_entity(session, DBTopic, topic_id, "Topic not found")
        return Topic(**db_topic.to_dict())


async def list_topic(offset: int, limit: int) -> list[Topic]:
    async with SessionLocal() as session:
        stmt = select(DBTopic).order_by(DBTopic.id.asc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        db_topics = result.scalars().all()
        return [Topic(**db_topic.to_dict()) for db_topic in db_topics]


async def delete_topic(topic_id) -> None:
    async with SessionLocal() as session:
        await _delete_entity(session, DBTopic, topic_id, "Topic not found")


async def create_subscription(data: CreateSubscription) -> Subscription:
    async with SessionLocal() as session:
        db_subscription = DBSubscription(
            id=data.id,
            topic_id=data.topic_id,
            filter=data.filter,
            max_delivery_attempts=data.max_delivery_attempts,
            backoff_min_seconds=data.backoff_min_seconds,
            backoff_max_seconds=data.backoff_max_seconds,
            created_at=utc_now(),
        )
        session.add(db_subscription)

        try:
            await session.commit()
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise AlreadyExistsError("This subscription already exists") from None
            if is_foreign_key_violation(exc):
                raise NotFoundError("Topic not found") from None
            raise

        return Subscription(**db_subscription.to_dict())


async def get_subscription(subscription_id: str) -> Subscription:
    async with SessionLocal() as session:
        db_subscription = await _get_entity(session, DBSubscription, subscription_id, "Subscription not found")
        return Subscription(**db_subscription.to_dict())


async def list_subscription(offset: int, limit: int) -> list[Subscription]:
    async with SessionLocal() as session:
        stmt = select(DBSubscription).order_by(DBSubscription.id.asc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        db_subscriptions = result.scalars().all()
        return [Subscription(**db_subscription.to_dict()) for db_subscription in db_subscriptions]


async def delete_subscription(subscription_id: str) -> None:
    async with SessionLocal() as session:
        await _delete_entity(session, DBSubscription, subscription_id, "Subscription not found")


async def publish_messages(topic_id: str, messages: list[dict[str, Any]]) -> int:
    query = "SELECT publish_messages(:topic_id, CAST(:messages AS jsonb[]))"
    stmt = text(query).bindparams(topic_id=topic_id, messages=messages)
    jsonb_array = [Json(m) for m in messages]

    async with SessionLocal() as session:
        result = await session.execute(
            stmt,
            {"topic_id": topic_id, "messages": jsonb_array},
        )
        count = result.scalar_one()
        await session.commit()

    return count


async def consume_messages(subscription_id: str, consumer_id: str, batch_size: int) -> list[Message]:
    query = "SELECT * FROM consume_messages(:subscription_id, :consumer_id, :batch_size)"
    stmt = text(query)

    async with SessionLocal() as session:
        result = await session.execute(
            stmt,
            {
                "subscription_id": subscription_id,
                "consumer_id": consumer_id,
                "batch_size": batch_size,
            },
        )
        rows = result.mappings().all()
        await session.commit()

    return [Message(**row) for row in rows]


async def ack_messages(subscription_id: str, message_ids: list[uuid.UUID]) -> bool:
    query = "SELECT ack_messages(:subscription_id, :message_ids)"
    return await _execute_sql_command(query, {"subscription_id": subscription_id, "message_ids": message_ids})


async def nack_messages(subscription_id: str, message_ids: list[uuid.UUID]) -> bool:
    query = "SELECT nack_messages(:subscription_id, :message_ids)"
    return await _execute_sql_command(query, {"subscription_id": subscription_id, "message_ids": message_ids})


async def list_dlq_messages(subscription_id: str, offset: int = 0, limit: int = 100) -> list[Message]:
    query = "SELECT * FROM list_dlq_messages(:subscription_id, :offset, :limit)"
    stmt = text(query)

    async with SessionLocal() as session:
        result = await session.execute(
            stmt,
            {
                "subscription_id": subscription_id,
                "offset": offset,
                "limit": limit,
            },
        )
        rows = result.mappings().all()

    return [Message(**row) for row in rows]


async def reprocess_dlq_messages(subscription_id: str, message_ids: list[uuid.UUID]) -> bool:
    query = "SELECT reprocess_dlq_messages(:subscription_id, :message_ids)"
    return await _execute_sql_command(query, {"subscription_id": subscription_id, "message_ids": message_ids})


async def cleanup_stuck_messages(lock_timeout_seconds: int) -> bool:
    query = "SELECT cleanup_stuck_messages(make_interval(secs => :timeout))"
    return await _execute_sql_command(query, {"timeout": lock_timeout_seconds})


async def cleanup_acked_messages(older_than_seconds: int) -> bool:
    query = "SELECT cleanup_acked_messages(make_interval(secs => :older_than))"
    return await _execute_sql_command(query, {"older_than": older_than_seconds})


async def subscription_metrics(subscription_id: str) -> SubscriptionMetrics:
    query = "SELECT * FROM subscription_metrics(:subscription_id)"
    stmt = text(query)

    async with SessionLocal() as session:
        result = await session.execute(stmt, {"subscription_id": subscription_id})
        row = result.mappings().one()
        result_dict = dict(row)
        result_dict["subscription_id"] = subscription_id

    return SubscriptionMetrics(**result_dict)


async def database_ping() -> bool:
    async with SessionLocal() as session:
        result = await session.scalar(select(1))
    return result == 1
