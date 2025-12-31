import uuid
from typing import Any

from psycopg.types.json import Json
from sqlalchemy import select, text

from fastpubsub.database import SessionLocal
from fastpubsub.models import Message, SubscriptionMetrics
from fastpubsub.services.helpers import _execute_sql_command


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
