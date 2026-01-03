"""Helper functions for service layer operations."""

import datetime
import time
import uuid

from sqlalchemy import select, text

from fastpubsub.database import SessionLocal
from fastpubsub.exceptions import NotFoundError
from fastpubsub.logger import get_logger

logger = get_logger(__name__)


def utc_now():
    """Get current UTC timestamp.

    Returns:
        Current datetime with UTC timezone.
    """
    return datetime.datetime.now(datetime.UTC)


async def _get_entity(
    session, model, entity_id: str | uuid.UUID, error_message: str, raise_exception: bool = True
):
    """Generic helper to get an entity by ID or raise NotFoundError.

    Args:
        session: Database session to use for the query.
        model: SQLAlchemy model class to query.
        entity_id: ID of the entity to retrieve.
        error_message: Error message to include in NotFoundError.
        raise_exception: Whether to raise NotFoundError if entity is not found.

    Returns:
        The entity instance if found, None if not found and raise_exception is False.

    Raises:
        NotFoundError: If entity is not found and raise_exception is True.
    """
    stmt = select(model).filter_by(id=entity_id)
    result = await session.execute(stmt)
    entity = result.scalar_one_or_none()
    if entity is None and raise_exception:
        raise NotFoundError(error_message) from None
    return entity


async def _delete_entity(session, model, entity_id: str | uuid.UUID, error_message: str) -> None:
    """Generic helper to delete an entity by ID or raise NotFoundError.

    Args:
        session: Database session to use for the operation.
        model: SQLAlchemy model class to delete from.
        entity_id: ID of the entity to delete.
        error_message: Error message to include in NotFoundError.

    Raises:
        NotFoundError: If entity with the given ID doesn't exist.
    """
    entity = await _get_entity(session, model, entity_id, error_message)
    await session.delete(entity)
    await session.commit()


async def _execute_sql_command(query: str, params: dict) -> bool:
    """Generic helper to execute SQL commands.

    Executes a SQL command and returns True if exactly one row was affected,
    False otherwise. This is used for message acknowledgment and similar
    operations where exactly one row is expected to be modified.

    Args:
        query: SQL query to execute
        params: Query parameters

    Returns:
        True if exactly one row was affected, False otherwise
    """
    start_time = time.perf_counter()
    stmt = text(query)

    try:
        async with SessionLocal() as session:
            result = await session.execute(stmt, params)
            rowcount = result.rowcount
            await session.commit()

        duration = time.perf_counter() - start_time

        # Log slow database operations (>100ms)
        if duration > 0.1:
            logger.warning(
                "slow database operation",
                extra={
                    "query": query[:100] + "..." if len(query) > 100 else query,
                    "params": str(params)[:200] + "..." if len(str(params)) > 200 else str(params),
                    "rowcount": rowcount,
                    "duration": f"{duration:.4f}s",
                },
            )
        elif duration > 0.01:  # Log operations >10ms at debug level
            logger.debug(
                "database operation completed",
                extra={
                    "query": query[:50] + "..." if len(query) > 50 else query,
                    "rowcount": rowcount,
                    "duration": f"{duration:.4f}s",
                },
            )

        return rowcount == 1
    except Exception as e:
        duration = time.perf_counter() - start_time
        logger.error(
            "database operation failed",
            extra={
                "query": query[:100] + "..." if len(query) > 100 else query,
                "params": str(params)[:200] + "..." if len(str(params)) > 200 else str(params),
                "error": str(e),
                "duration": f"{duration:.4f}s",
            },
        )
        raise
