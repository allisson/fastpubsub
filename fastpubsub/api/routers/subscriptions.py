from uuid import UUID

from fastapi import APIRouter, Query, status

from fastpubsub import models, services

router = APIRouter(prefix="/subscriptions", tags=["subscriptions"])


@router.post(
    "",
    response_model=models.Subscription,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": models.AlreadyExists}},
    summary="Create a subscription",
)
async def create_subscription(data: models.CreateSubscription):
    return await services.create_subscription(data)


@router.get(
    "/{id}",
    response_model=models.Subscription,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    summary="Get a subscription",
)
async def get_subscription(id: str):
    return await services.get_subscription(id)


@router.get(
    "",
    response_model=models.ListSubscriptionAPI,
    status_code=status.HTTP_200_OK,
    summary="List subscriptions",
)
async def list_subscription(
    offset: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=100)
):
    subscriptions = await services.list_subscription(offset, limit)
    return models.ListSubscriptionAPI(data=subscriptions)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    summary="Delete subscription",
)
async def delete_subscription(id: str):
    await services.delete_subscription(id)


@router.get(
    "/{id}/messages",
    response_model=models.ListMessageAPI,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    summary="Get messages",
)
async def consume_messages(id: str, consumer_id: str, batch_size: int = Query(default=10, ge=1, le=100)):
    subscription = await get_subscription(id)
    messages = await services.consume_messages(
        subscription_id=subscription.id, consumer_id=consumer_id, batch_size=batch_size
    )
    return models.ListMessageAPI(data=messages)


@router.post(
    "/{id}/acks",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    summary="Ack messages",
)
async def ack_messages(id: str, data: list[UUID]):
    subscription = await get_subscription(id)
    await services.ack_messages(subscription_id=subscription.id, message_ids=data)


@router.post(
    "/{id}/nacks",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    summary="Nack messages",
)
async def nack_messages(id: str, data: list[UUID]):
    subscription = await get_subscription(id)
    await services.nack_messages(subscription_id=subscription.id, message_ids=data)


@router.get(
    "/{id}/dlq",
    response_model=models.ListMessageAPI,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    summary="List dlq messages",
)
async def list_dlq(
    id: str, offset: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=100)
):
    subscription = await get_subscription(id)
    messages = await services.list_dlq_messages(subscription_id=subscription.id, offset=offset, limit=limit)
    return models.ListMessageAPI(data=messages)


@router.post(
    "/{id}/dlq/reprocess",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    summary="Reprocess dlq messages",
)
async def reprocess_dlq(id: str, data: list[UUID]):
    subscription = await get_subscription(id)
    await services.reprocess_dlq_messages(subscription_id=subscription.id, message_ids=data)


@router.get(
    "/{id}/metrics",
    response_model=models.SubscriptionMetrics,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    summary="Get subscription metrics",
)
async def subscription_metrics(id: str):
    subscription = await get_subscription(id)
    return await services.subscription_metrics(subscription_id=subscription.id)
