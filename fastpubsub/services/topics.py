"""Topic management services for creating and managing pub/sub topics."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from fastpubsub.database import is_unique_violation, SessionLocal
from fastpubsub.database import Topic as DBTopic
from fastpubsub.exceptions import AlreadyExistsError
from fastpubsub.models import CreateTopic, Topic
from fastpubsub.services.helpers import _delete_entity, _get_entity, utc_now


async def create_topic(data: CreateTopic) -> Topic:
    """Create a new topic in the pub/sub system.

    Args:
        data: Topic creation data including the unique topic ID.

    Returns:
        Topic model with the created topic details.

    Raises:
        AlreadyExistsError: If a topic with the same ID already exists.
    """
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
    """Retrieve a topic by ID.

    Args:
        topic_id: ID of the topic to retrieve.

    Returns:
        Topic model with full topic details.

    Raises:
        NotFoundError: If no topic with the given ID exists.
    """
    async with SessionLocal() as session:
        db_topic = await _get_entity(session, DBTopic, topic_id, "Topic not found")
        return Topic(**db_topic.to_dict())


async def list_topic(offset: int, limit: int) -> list[Topic]:
    """List topics with pagination support.

    Args:
        offset: Number of items to skip for pagination.
        limit: Maximum number of items to return.

    Returns:
        List of Topic models.
    """
    async with SessionLocal() as session:
        stmt = select(DBTopic).order_by(DBTopic.id.asc()).offset(offset).limit(limit)
        result = await session.execute(stmt)
        db_topics = result.scalars().all()
        return [Topic(**db_topic.to_dict()) for db_topic in db_topics]


async def delete_topic(topic_id: str) -> None:
    """Delete a topic by ID.

    Args:
        topic_id: ID of the topic to delete.

    Raises:
        NotFoundError: If no topic with the given ID exists.
    """
    async with SessionLocal() as session:
        await _delete_entity(session, DBTopic, topic_id, "Topic not found")
