"""Message operations service for publishing, consuming, and managing pub/sub messages."""

import uuid
from typing import Any

from psycopg.types.json import Json
from sqlalchemy import select, text

from fastpubsub.database import SessionLocal
from fastpubsub.models import Message, SubscriptionMetrics
from fastpubsub.services.helpers import _execute_sql_command


async def publish_messages(topic_id: str, messages: list[dict[str, Any]]) -> int:
    """Publish messages to a topic.

    Args:
        topic_id: ID of the topic to publish messages to.
        messages: List of message dictionaries to publish.

    Returns:
        Number of messages successfully published.
    """
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
    """Consume messages from a subscription.

    Args:
        subscription_id: ID of the subscription to consume from.
        consumer_id: Unique identifier for the consumer.
        batch_size: Number of messages to retrieve.

    Returns:
        List of available messages for consumption.
    """
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
    """Acknowledge successful processing of messages.

    Args:
        subscription_id: ID of the subscription.
        message_ids: List of message UUIDs to acknowledge.

    Returns:
        True if exactly one row was affected, False otherwise.
    """
    query = "SELECT ack_messages(:subscription_id, :message_ids)"
    return await _execute_sql_command(query, {"subscription_id": subscription_id, "message_ids": message_ids})


async def nack_messages(subscription_id: str, message_ids: list[uuid.UUID]) -> bool:
    """Negative acknowledgment of message processing failure.

    Args:
        subscription_id: ID of the subscription.
        message_ids: List of message UUIDs to negatively acknowledge.

    Returns:
        True if exactly one row was affected, False otherwise.
    """
    query = "SELECT nack_messages(:subscription_id, :message_ids)"
    return await _execute_sql_command(query, {"subscription_id": subscription_id, "message_ids": message_ids})


async def list_dlq_messages(subscription_id: str, offset: int = 0, limit: int = 100) -> list[Message]:
    """List messages in the dead letter queue.

    Args:
        subscription_id: ID of the subscription.
        offset: Number of items to skip for pagination.
        limit: Maximum number of items to return.

    Returns:
        List of messages in the DLQ.
    """
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
    """Move dead letter queue messages back to active processing.

    Args:
        subscription_id: ID of the subscription.
        message_ids: List of message UUIDs to reprocess.

    Returns:
        True if exactly one row was affected, False otherwise.
    """
    query = "SELECT reprocess_dlq_messages(:subscription_id, :message_ids)"
    return await _execute_sql_command(query, {"subscription_id": subscription_id, "message_ids": message_ids})


async def cleanup_stuck_messages(lock_timeout_seconds: int) -> bool:
    """Unlock messages that have been locked for too long.

    Args:
        lock_timeout_seconds: Timeout threshold for stuck messages.

    Returns:
        True if cleanup was successful, False otherwise.
    """
    query = "SELECT cleanup_stuck_messages(make_interval(secs => :timeout))"
    return await _execute_sql_command(query, {"timeout": lock_timeout_seconds})


async def cleanup_acked_messages(older_than_seconds: int) -> bool:
    """Remove acknowledged messages older than the threshold.

    Args:
        older_than_seconds: Age threshold for message cleanup.

    Returns:
        True if cleanup was successful, False otherwise.
    """
    query = "SELECT cleanup_acked_messages(make_interval(secs => :older_than))"
    return await _execute_sql_command(query, {"older_than": older_than_seconds})


async def subscription_metrics(subscription_id: str) -> SubscriptionMetrics:
    """Get metrics and statistics for a subscription.

    Args:
        subscription_id: ID of the subscription.

    Returns:
        SubscriptionMetrics containing message counts by state.
    """
    query = "SELECT * FROM subscription_metrics(:subscription_id)"
    stmt = text(query)

    async with SessionLocal() as session:
        result = await session.execute(stmt, {"subscription_id": subscription_id})
        row = result.mappings().one()
        result_dict = dict(row)
        result_dict["subscription_id"] = subscription_id

    return SubscriptionMetrics(**result_dict)


async def database_ping() -> bool:
    """Check database connectivity.

    Returns:
        True if database is reachable, False otherwise.
    """
    async with SessionLocal() as session:
        result = await session.scalar(select(1))
    return result == 1
