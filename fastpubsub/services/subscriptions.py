"""Subscription management services for creating and managing topic subscriptions."""

import time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from fastpubsub.database import is_foreign_key_violation, is_unique_violation, SessionLocal
from fastpubsub.database import Subscription as DBSubscription
from fastpubsub.exceptions import AlreadyExistsError, NotFoundError
from fastpubsub.logger import get_logger
from fastpubsub.models import CreateSubscription, Subscription
from fastpubsub.services.helpers import _delete_entity, _get_entity, utc_now

logger = get_logger(__name__)


async def create_subscription(data: CreateSubscription) -> Subscription:
    """Create a new subscription to a topic.

    Args:
        data: Subscription creation data including ID, topic ID, filter, and delivery settings.

    Returns:
        Subscription model with the created subscription details.

    Raises:
        AlreadyExistsError: If a subscription with the same ID already exists.
        NotFoundError: If the specified topic doesn't exist.
    """
    start_time = time.perf_counter()
    logger.info(
        "creating subscription",
        extra={
            "subscription_id": data.id,
            "topic_id": data.topic_id,
            "max_delivery_attempts": data.max_delivery_attempts,
        },
    )

    try:
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
                    logger.warning(
                        "subscription creation failed: subscription already exists",
                        extra={"subscription_id": data.id, "topic_id": data.topic_id},
                    )
                    raise AlreadyExistsError("This subscription already exists") from None
                if is_foreign_key_violation(exc):
                    logger.warning(
                        "subscription creation failed: topic not found",
                        extra={"subscription_id": data.id, "topic_id": data.topic_id},
                    )
                    raise NotFoundError("Topic not found") from None
                raise

        duration = time.perf_counter() - start_time
        logger.info(
            "subscription created",
            extra={"subscription_id": data.id, "topic_id": data.topic_id, "duration": f"{duration:.4f}s"},
        )
        return Subscription(**db_subscription.to_dict())
    except (AlreadyExistsError, NotFoundError):
        raise
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(
            "subscription creation failed",
            extra={
                "subscription_id": data.id,
                "topic_id": data.topic_id,
                "error": str(e),
                "duration": f"{duration:.4f}s",
            },
        )
        raise


async def get_subscription(subscription_id: str) -> Subscription:
    """Retrieve a subscription by ID.

    Args:
        subscription_id: ID of the subscription to retrieve.

    Returns:
        Subscription model with full subscription details.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
    """
    start_time = time.perf_counter()
    logger.debug("getting subscription", extra={"subscription_id": subscription_id})

    try:
        async with SessionLocal() as session:
            db_subscription = await _get_entity(
                session, DBSubscription, subscription_id, "Subscription not found"
            )

        duration = time.perf_counter() - start_time
        logger.debug(
            "subscription retrieved",
            extra={
                "subscription_id": subscription_id,
                "topic_id": db_subscription.topic_id,
                "duration": f"{duration:.4f}s",
            },
        )
        return Subscription(**db_subscription.to_dict())
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.warning(
            "subscription retrieval failed",
            extra={"subscription_id": subscription_id, "error": str(e), "duration": f"{duration:.4f}s"},
        )
        raise


async def list_subscription(offset: int, limit: int) -> list[Subscription]:
    """List subscriptions with pagination support.

    Args:
        offset: Number of items to skip for pagination.
        limit: Maximum number of items to return.

    Returns:
        List of Subscription models.
    """
    start_time = time.perf_counter()
    logger.debug("listing subscriptions", extra={"offset": offset, "limit": limit})

    try:
        async with SessionLocal() as session:
            stmt = select(DBSubscription).order_by(DBSubscription.id.asc()).offset(offset).limit(limit)
            result = await session.execute(stmt)
            db_subscriptions = result.scalars().all()

        subscriptions = [Subscription(**db_subscription.to_dict()) for db_subscription in db_subscriptions]
        duration = time.perf_counter() - start_time
        logger.debug(
            "subscriptions listed",
            extra={
                "offset": offset,
                "limit": limit,
                "returned_count": len(subscriptions),
                "duration": f"{duration:.4f}s",
            },
        )
        return subscriptions
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(
            "subscription listing failed",
            extra={"offset": offset, "limit": limit, "error": str(e), "duration": f"{duration:.4f}s"},
        )
        raise


async def delete_subscription(subscription_id: str) -> None:
    """Delete a subscription by ID.

    Args:
        subscription_id: ID of the subscription to delete.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
    """
    start_time = time.perf_counter()
    logger.info("deleting subscription", extra={"subscription_id": subscription_id})

    try:
        async with SessionLocal() as session:
            await _delete_entity(session, DBSubscription, subscription_id, "Subscription not found")

        duration = time.perf_counter() - start_time
        logger.info(
            "subscription deleted", extra={"subscription_id": subscription_id, "duration": f"{duration:.4f}s"}
        )
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(
            "subscription deletion failed",
            extra={"subscription_id": subscription_id, "error": str(e), "duration": f"{duration:.4f}s"},
        )
        raise
