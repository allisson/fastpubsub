"""API endpoints for topic management and message publishing operations."""

from typing import Annotated, Any

from fastapi import APIRouter, Depends, Query, status

from fastpubsub import models, services

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post(
    "",
    response_model=models.Topic,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": models.GenericError}},
    summary="Create a new topic",
)
async def create_topic(
    data: models.CreateTopic,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("topics", "create"))],
):
    """Create a new topic in the pub/sub system.

    Creates a topic that can be used to organize and publish messages.
    Subscriptions can be created to consume messages from topics.

    Args:
        data: Topic creation data including the unique topic ID.
        token: Decoded client token with 'topics:create' scope.

    Returns:
        Topic model with the created topic details.

    Raises:
        AlreadyExistsError: If a topic with the same ID already exists.
        InvalidClient: If the requesting client lacks 'topics:create' scope.
    """
    return await services.create_topic(data)


@router.get(
    "/{id}",
    response_model=models.Topic,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.GenericError}},
    summary="Get a topic",
)
async def get_topic(
    id: str, token: Annotated[models.DecodedClientToken, Depends(services.require_scope("topics", "read"))]
):
    """Retrieve a topic by ID.

    Returns the full details of an existing topic including ID and creation timestamp.

    Args:
        id: String ID of the topic to retrieve.
        token: Decoded client token with 'topics:read' scope.

    Returns:
        Topic model with full topic details.

    Raises:
        NotFoundError: If no topic with the given ID exists.
        InvalidClient: If the requesting client lacks 'topics:read' scope.
    """
    return await services.get_topic(id)


@router.get(
    "",
    response_model=models.ListTopicAPI,
    status_code=status.HTTP_200_OK,
    summary="List topics",
)
async def list_topic(
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("topics", "read"))],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    """List topics with pagination support.

    Returns a paginated list of all topics in the system.

    Args:
        token: Decoded client token with 'topics:read' scope.
        offset: Number of items to skip (for pagination).
        limit: Maximum number of items to return (1-100).

    Returns:
        ListTopicAPI containing the list of topics.

    Raises:
        InvalidClient: If the requesting client lacks 'topics:read' scope.
    """
    topics = await services.list_topic(offset, limit)
    return models.ListTopicAPI(data=topics)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.GenericError}},
    summary="Delete a topic",
)
async def delete_topic(
    id: str, token: Annotated[models.DecodedClientToken, Depends(services.require_scope("topics", "delete"))]
):
    """Delete a topic by ID.

    Permanently removes a topic from the system. This action cannot be undone
    and will also remove all subscriptions and messages associated with the topic.

    Args:
        id: String ID of the topic to delete.
        token: Decoded client token with 'topics:delete' scope.

    Raises:
        NotFoundError: If no topic with the given ID exists.
        InvalidClient: If the requesting client lacks 'topics:delete' scope.
    """
    await services.delete_topic(id)


@router.post(
    "/{id}/messages",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.GenericError}},
    summary="Post messages",
)
async def publish_messages(
    id: str,
    data: list[dict[str, Any]],
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("topics", "publish"))],
):
    """Publish messages to a topic.

    Publishes one or more messages to a topic, making them available
    for consumption by subscriptions to that topic.

    Args:
        id: String ID of the topic to publish to.
        data: List of message dictionaries to publish.
        token: Decoded client token with 'topics:publish' scope.

    Returns:
        Integer count of messages successfully published.

    Raises:
        NotFoundError: If no topic with the given ID exists.
        InvalidClient: If the requesting client lacks 'topics:publish' scope.
    """
    topic = await services.get_topic(id)
    return await services.publish_messages(topic_id=topic.id, messages=data)
