"""Topic management services for creating and managing pub/sub topics."""

import time

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from fastpubsub.database import is_unique_violation, SessionLocal
from fastpubsub.database import Topic as DBTopic
from fastpubsub.exceptions import AlreadyExistsError
from fastpubsub.logger import get_logger
from fastpubsub.models import CreateTopic, Topic
from fastpubsub.services.helpers import _delete_entity, _get_entity, utc_now

logger = get_logger(__name__)


async def create_topic(data: CreateTopic) -> Topic:
    """Create a new topic in the pub/sub system.

    Args:
        data: Topic creation data including the unique topic ID.

    Returns:
        Topic model with the created topic details.

    Raises:
        AlreadyExistsError: If a topic with the same ID already exists.
    """
    start_time = time.perf_counter()
    logger.info("creating topic", extra={"topic_id": data.id})

    try:
        async with SessionLocal() as session:
            db_topic = DBTopic(id=data.id, created_at=utc_now())
            session.add(db_topic)

            try:
                await session.commit()
            except IntegrityError as exc:
                if is_unique_violation(exc):
                    logger.warning("topic creation failed: topic already exists", extra={"topic_id": data.id})
                    raise AlreadyExistsError("This topic already exists") from None
                raise

        duration = time.perf_counter() - start_time
        logger.info("topic created", extra={"topic_id": data.id, "duration": f"{duration:.4f}s"})
        return Topic(**db_topic.to_dict())
    except AlreadyExistsError:
        raise
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(
            "topic creation failed",
            extra={"topic_id": data.id, "error": str(e), "duration": f"{duration:.4f}s"},
        )
        raise


async def get_topic(topic_id: str) -> Topic:
    """Retrieve a topic by ID.

    Args:
        topic_id: ID of the topic to retrieve.

    Returns:
        Topic model with full topic details.

    Raises:
        NotFoundError: If no topic with the given ID exists.
    """
    start_time = time.perf_counter()
    logger.debug("getting topic", extra={"topic_id": topic_id})

    try:
        async with SessionLocal() as session:
            db_topic = await _get_entity(session, DBTopic, topic_id, "Topic not found")

        duration = time.perf_counter() - start_time
        logger.debug("topic retrieved", extra={"topic_id": topic_id, "duration": f"{duration:.4f}s"})
        return Topic(**db_topic.to_dict())
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.warning(
            "topic retrieval failed",
            extra={"topic_id": topic_id, "error": str(e), "duration": f"{duration:.4f}s"},
        )
        raise


async def list_topic(offset: int, limit: int) -> list[Topic]:
    """List topics with pagination support.

    Args:
        offset: Number of items to skip for pagination.
        limit: Maximum number of items to return.

    Returns:
        List of Topic models.
    """
    start_time = time.perf_counter()
    logger.debug("listing topics", extra={"offset": offset, "limit": limit})

    try:
        async with SessionLocal() as session:
            stmt = select(DBTopic).order_by(DBTopic.id.asc()).offset(offset).limit(limit)
            result = await session.execute(stmt)
            db_topics = result.scalars().all()

        topics = [Topic(**db_topic.to_dict()) for db_topic in db_topics]
        duration = time.perf_counter() - start_time
        logger.debug(
            "topics listed",
            extra={
                "offset": offset,
                "limit": limit,
                "returned_count": len(topics),
                "duration": f"{duration:.4f}s",
            },
        )
        return topics
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(
            "topic listing failed",
            extra={"offset": offset, "limit": limit, "error": str(e), "duration": f"{duration:.4f}s"},
        )
        raise


async def delete_topic(topic_id: str) -> None:
    """Delete a topic by ID.

    Args:
        topic_id: ID of the topic to delete.

    Raises:
        NotFoundError: If no topic with the given ID exists.
    """
    start_time = time.perf_counter()
    logger.info("deleting topic", extra={"topic_id": topic_id})

    try:
        async with SessionLocal() as session:
            await _delete_entity(session, DBTopic, topic_id, "Topic not found")

        duration = time.perf_counter() - start_time
        logger.info("topic deleted", extra={"topic_id": topic_id, "duration": f"{duration:.4f}s"})
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(
            "topic deletion failed",
            extra={"topic_id": topic_id, "error": str(e), "duration": f"{duration:.4f}s"},
        )
        raise
