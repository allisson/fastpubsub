"""API endpoints for subscription management and message operations."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status

from fastpubsub import models, services

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "",
    response_model=models.Subscription,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": models.GenericError}},
    summary="Create a subscription",
)
async def create_subscription(
    data: models.CreateSubscription,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "create"))],
):
    """Create a new subscription to a topic.

    Creates a subscription that defines how messages from a topic should be consumed,
    including filtering, delivery attempts, and backoff configuration.

    Args:
        data: Subscription creation data including ID, topic ID, filter, and delivery settings.
        token: Decoded client token with 'subscriptions:create' scope.

    Returns:
        Subscription model with the created subscription details.

    Raises:
        AlreadyExistsError: If a subscription with the same ID already exists.
        NotFoundError: If the specified topic doesn't exist.
        InvalidClient: If the requesting client lacks 'subscriptions:create' scope.
    """
    return await services.create_subscription(data)


@router.get(
    "/{id}",
    response_model=models.Subscription,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.GenericError}},
    summary="Get a subscription",
)
async def get_subscription(
    id: str,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "read"))],
):
    """Retrieve a subscription by ID.

    Returns the full details of an existing subscription including ID, topic ID,
    filter configuration, delivery attempts, and backoff settings.

    Args:
        id: String ID of the subscription to retrieve.
        token: Decoded client token with 'subscriptions:read' scope.

    Returns:
        Subscription model with full subscription details.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
        InvalidClient: If the requesting client lacks 'subscriptions:read' scope.
    """
    return await services.get_subscription(id)


@router.get(
    "",
    response_model=models.ListSubscriptionAPI,
    status_code=status.HTTP_200_OK,
    summary="List subscriptions",
)
async def list_subscription(
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "read"))],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    """List subscriptions with pagination support.

    Returns a paginated list of all subscriptions in the system.

    Args:
        token: Decoded client token with 'subscriptions:read' scope.
        offset: Number of items to skip (for pagination).
        limit: Maximum number of items to return (1-100).

    Returns:
        ListSubscriptionAPI containing the list of subscriptions.

    Raises:
        InvalidClient: If the requesting client lacks 'subscriptions:read' scope.
    """
    subscriptions = await services.list_subscription(offset, limit)
    return models.ListSubscriptionAPI(data=subscriptions)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.GenericError}},
    summary="Delete subscription",
)
async def delete_subscription(
    id: str,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "delete"))],
):
    """Delete a subscription by ID.

    Permanently removes a subscription from the system. This action cannot be undone
    and will also remove all messages associated with the subscription.

    Args:
        id: String ID of the subscription to delete.
        token: Decoded client token with 'subscriptions:delete' scope.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
        InvalidClient: If the requesting client lacks 'subscriptions:delete' scope.
    """
    await services.delete_subscription(id)


@router.get(
    "/{id}/messages",
    response_model=models.ListMessageAPI,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.GenericError}},
    summary="Get messages",
)
async def consume_messages(
    id: str,
    consumer_id: str,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "consume"))],
    batch_size: int = Query(default=10, ge=1, le=100),
):
    """Consume messages from a subscription.

    Retrieves messages from the subscription queue that are available for processing.
    Messages are locked to the consumer to prevent duplicate processing.

    Args:
        id: String ID of the subscription to consume from.
        consumer_id: Unique identifier for the consumer instance.
        token: Decoded client token with 'subscriptions:consume' scope.
        batch_size: Number of messages to retrieve (1-100).

    Returns:
        ListMessageAPI containing the available messages.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
        InvalidClient: If the requesting client lacks 'subscriptions:consume' scope.
    """
    subscription = await get_subscription(id, token)
    messages = await services.consume_messages(
        subscription_id=subscription.id, consumer_id=consumer_id, batch_size=batch_size
    )
    return models.ListMessageAPI(data=messages)


@router.post(
    "/{id}/acks",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.GenericError}},
    summary="Ack messages",
)
async def ack_messages(
    id: str,
    data: list[UUID],
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "consume"))],
):
    """Acknowledge successful processing of messages.

    Marks messages as successfully processed, removing them from the queue.
    Acknowledged messages will not be delivered again.

    Args:
        id: String ID of the subscription.
        data: List of message UUIDs to acknowledge.
        token: Decoded client token with 'subscriptions:consume' scope.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
        InvalidClient: If the requesting client lacks 'subscriptions:consume' scope.
    """
    subscription = await get_subscription(id, token)
    await services.ack_messages(subscription_id=subscription.id, message_ids=data)


@router.post(
    "/{id}/nacks",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.GenericError}},
    summary="Nack messages",
)
async def nack_messages(
    id: str,
    data: list[UUID],
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "consume"))],
):
    """Negative acknowledgment of message processing failure.

    Marks messages as failed, making them available for redelivery.
    The message will be redelivered according to the subscription's backoff configuration.

    Args:
        id: String ID of the subscription.
        data: List of message UUIDs to negatively acknowledge.
        token: Decoded client token with 'subscriptions:consume' scope.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
        InvalidClient: If the requesting client lacks 'subscriptions:consume' scope.
    """
    subscription = await get_subscription(id, token)
    await services.nack_messages(subscription_id=subscription.id, message_ids=data)


@router.get(
    "/{id}/dlq",
    response_model=models.ListMessageAPI,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.GenericError}},
    summary="List dlq messages",
)
async def list_dlq(
    id: str,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "consume"))],
    offset: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    """List messages in the dead letter queue.

    Retrieves messages that have failed delivery after exceeding the maximum
    number of delivery attempts and have been moved to the DLQ.

    Args:
        id: String ID of the subscription.
        token: Decoded client token with 'subscriptions:consume' scope.
        offset: Number of items to skip (for pagination).
        limit: Maximum number of items to return (1-100).

    Returns:
        ListMessageAPI containing the DLQ messages.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
        InvalidClient: If the requesting client lacks 'subscriptions:consume' scope.
    """
    subscription = await get_subscription(id, token)
    messages = await services.list_dlq_messages(subscription_id=subscription.id, offset=offset, limit=limit)
    return models.ListMessageAPI(data=messages)


@router.post(
    "/{id}/dlq/reprocess",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.GenericError}},
    summary="Reprocess dlq messages",
)
async def reprocess_dlq(
    id: str,
    data: list[UUID],
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "consume"))],
):
    """Move dead letter queue messages back to active processing.

    Reprocesses messages from the DLQ by moving them back to the main queue
    for another attempt at delivery.

    Args:
        id: String ID of the subscription.
        data: List of message UUIDs to reprocess.
        token: Decoded client token with 'subscriptions:consume' scope.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
        InvalidClient: If the requesting client lacks 'subscriptions:consume' scope.
    """
    subscription = await get_subscription(id, token)
    await services.reprocess_dlq_messages(subscription_id=subscription.id, message_ids=data)


@router.get(
    "/{id}/metrics",
    response_model=models.SubscriptionMetrics,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.GenericError}},
    summary="Get subscription metrics",
)
async def subscription_metrics(
    id: str,
    token: Annotated[models.DecodedClientToken, Depends(services.require_scope("subscriptions", "read"))],
):
    """Get metrics and statistics for a subscription.

    Returns counts of messages in different states for monitoring and analysis.

    Args:
        id: String ID of the subscription.
        token: Decoded client token with 'subscriptions:read' scope.

    Returns:
        SubscriptionMetrics containing message counts by state.

    Raises:
        NotFoundError: If no subscription with the given ID exists.
        InvalidClient: If the requesting client lacks 'subscriptions:read' scope.
    """
    subscription = await get_subscription(id, token)
    return await services.subscription_metrics(subscription_id=subscription.id)
