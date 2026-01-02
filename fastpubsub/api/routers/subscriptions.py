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
    subscription = await get_subscription(id, token)
    return await services.subscription_metrics(subscription_id=subscription.id)
