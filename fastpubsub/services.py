import datetime
import uuid
from typing import Any

from psycopg.types.json import Json
from sqlalchemy import text
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


def create_topic(data: CreateTopic) -> Topic:
    with SessionLocal() as session:
        db_topic = DBTopic(id=data.id, created_at=utc_now())
        session.add(db_topic)

        try:
            session.commit()
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise AlreadyExistsError("This topic already exists") from None
            raise

        return Topic(**db_topic.to_dict())


def get_topic(topic_id: str) -> Topic:
    with SessionLocal() as session:
        db_topic = session.query(DBTopic).filter_by(id=topic_id).one_or_none()
        if db_topic is None:
            raise NotFoundError("Topic not found") from None
        return Topic(**db_topic.to_dict())


def list_topic(offset: int, limit: int) -> list[Topic]:
    with SessionLocal() as session:
        db_topics = session.query(DBTopic).order_by(DBTopic.id.asc()).offset(offset).limit(limit)
        return [Topic(**db_topic.to_dict()) for db_topic in db_topics]


def delete_topic(topic_id) -> None:
    with SessionLocal() as session:
        db_topic = session.query(DBTopic).filter_by(id=topic_id).one_or_none()
        if db_topic is None:
            raise NotFoundError("Topic not found") from None
        session.delete(db_topic)
        session.commit()


def create_subscription(data: CreateSubscription) -> Subscription:
    with SessionLocal() as session:
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
            session.commit()
        except IntegrityError as exc:
            if is_unique_violation(exc):
                raise AlreadyExistsError("This subscription already exists") from None
            if is_foreign_key_violation(exc):
                raise NotFoundError("Topic not found") from None
            raise

        return Subscription(**db_subscription.to_dict())


def get_subscription(subscription_id: str) -> Subscription:
    with SessionLocal() as session:
        db_subscription = session.query(DBSubscription).filter_by(id=subscription_id).one_or_none()
        if db_subscription is None:
            raise NotFoundError("Subscription not found") from None
        return Subscription(**db_subscription.to_dict())


def list_subscription(offset: int, limit: int) -> list[Subscription]:
    with SessionLocal() as session:
        db_subscriptions = (
            session.query(DBSubscription).order_by(DBSubscription.id.asc()).offset(offset).limit(limit)
        )
        return [Subscription(**db_subscription.to_dict()) for db_subscription in db_subscriptions]


def delete_subscription(subscription_id: str) -> None:
    with SessionLocal() as session:
        db_subscription = session.query(DBSubscription).filter_by(id=subscription_id).one_or_none()
        if db_subscription is None:
            raise NotFoundError("Subscription not found")
        session.delete(db_subscription)
        session.commit()


def publish_messages(topic_id: str, messages: list[dict[str, Any]]) -> int:
    query = "SELECT publish_messages(:topic_id, CAST(:messages AS jsonb[]))"
    stmt = text(query).bindparams(topic_id=topic_id, messages=messages)
    jsonb_array = [Json(m) for m in messages]

    with SessionLocal() as session:
        result = session.execute(
            stmt,
            {"topic_id": topic_id, "messages": jsonb_array},
        ).scalar_one()
        session.commit()

    return result


def consume_messages(subscription_id: str, consumer_id: str, batch_size: int) -> list[Message]:
    query = "SELECT * FROM consume_messages(:subscription_id, :consumer_id, :batch_size)"
    stmt = text(query)

    with SessionLocal() as session:
        rows = (
            session.execute(
                stmt,
                {
                    "subscription_id": subscription_id,
                    "consumer_id": consumer_id,
                    "batch_size": batch_size,
                },
            )
            .mappings()
            .all()
        )
        session.commit()

    return [Message(**row) for row in rows]


def ack_messages(subscription_id: str, message_ids: list[uuid.UUID]) -> bool:
    query = "SELECT ack_messages(:subscription_id, :message_ids)"
    stmt = text(query)

    with SessionLocal() as session:
        result = session.execute(
            stmt,
            {
                "subscription_id": subscription_id,
                "message_ids": message_ids,
            },
        ).rowcount
        session.commit()

    return result == 1


def nack_messages(subscription_id: str, message_ids: list[uuid.UUID]) -> bool:
    query = "SELECT nack_messages(:subscription_id, :message_ids)"
    stmt = text(query)

    with SessionLocal() as session:
        result = session.execute(
            stmt,
            {
                "subscription_id": subscription_id,
                "message_ids": message_ids,
            },
        ).rowcount
        session.commit()

    return result == 1


def list_dlq_messages(subscription_id: str, offset: int = 0, limit: int = 100) -> list[Message]:
    query = "SELECT * FROM list_dlq_messages(:subscription_id, :offset, :limit)"
    stmt = text(query)

    with SessionLocal() as session:
        rows = (
            session.execute(
                stmt,
                {
                    "subscription_id": subscription_id,
                    "offset": offset,
                    "limit": limit,
                },
            )
            .mappings()
            .all()
        )

    return [Message(**row) for row in rows]


def reprocess_dlq_messages(subscription_id: str, message_ids: list[uuid.UUID]) -> bool:
    query = "SELECT reprocess_dlq_messages(:subscription_id, :message_ids)"
    stmt = text(query)

    with SessionLocal() as session:
        result = session.execute(
            stmt,
            {
                "subscription_id": subscription_id,
                "message_ids": message_ids,
            },
        ).rowcount
        session.commit()

    return result == 1


def cleanup_stuck_messages(lock_timeout_seconds: int) -> int:
    query = "SELECT cleanup_stuck_messages(make_interval(secs => :timeout))"
    stmt = text(query)

    with SessionLocal() as session:
        result = session.execute(
            stmt,
            {
                "timeout": lock_timeout_seconds,
            },
        ).rowcount
        session.commit()

    return result == 1


def cleanup_acked_messages(older_than_seconds: int) -> bool:
    query = "SELECT cleanup_acked_messages(make_interval(secs => :older_than))"
    stmt = text(query)

    with SessionLocal() as session:
        result = session.execute(
            stmt,
            {
                "older_than": older_than_seconds,
            },
        ).rowcount
        session.commit()

    return result == 1


def subscription_metrics(subscription_id: str) -> SubscriptionMetrics:
    query = "SELECT * FROM subscription_metrics(:subscription_id)"
    stmt = text(query)

    with SessionLocal() as session:
        row = session.execute(stmt, {"subscription_id": subscription_id}).mappings().one()
        result = dict(row)
        result["subscription_id"] = subscription_id

    return SubscriptionMetrics(**result)
