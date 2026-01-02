import datetime
import uuid

from sqlalchemy import select, text

from fastpubsub.database import SessionLocal
from fastpubsub.exceptions import NotFoundError


def utc_now():
    return datetime.datetime.now(datetime.UTC)


async def _get_entity(
    session, model, entity_id: str | uuid.UUID, error_message: str, raise_exception: bool = True
):
    """Generic helper to get an entity by ID or raise NotFoundError."""
    stmt = select(model).filter_by(id=entity_id)
    result = await session.execute(stmt)
    entity = result.scalar_one_or_none()
    if entity is None and raise_exception:
        raise NotFoundError(error_message) from None
    return entity


async def _delete_entity(session, model, entity_id: str | uuid.UUID, error_message: str) -> None:
    """Generic helper to delete an entity by ID or raise NotFoundError."""
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
    stmt = text(query)
    async with SessionLocal() as session:
        result = await session.execute(stmt, params)
        rowcount = result.rowcount
        await session.commit()
    return rowcount == 1
