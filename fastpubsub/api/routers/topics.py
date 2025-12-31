from typing import Any

from fastapi import APIRouter, Query, status

from fastpubsub import models, services

router = APIRouter(prefix="/topics", tags=["topics"])


@router.post(
    "",
    response_model=models.Topic,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": models.AlreadyExists}},
    summary="Create a new topic",
)
async def create_topic(data: models.CreateTopic):
    return await services.create_topic(data)


@router.get(
    "/{id}",
    response_model=models.Topic,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    summary="Get a topic",
)
async def get_topic(id: str):
    return await services.get_topic(id)


@router.get(
    "",
    response_model=models.ListTopicAPI,
    status_code=status.HTTP_200_OK,
    summary="List topics",
)
async def list_topic(offset: int = Query(default=0, ge=0), limit: int = Query(default=10, ge=1, le=100)):
    topics = await services.list_topic(offset, limit)
    return models.ListTopicAPI(data=topics)


@router.delete(
    "/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    summary="Delete a topic",
)
async def delete_topic(id: str):
    await services.delete_topic(id)


@router.post(
    "/{id}/messages",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    summary="Post messages",
)
async def publish_messages(id: str, data: list[dict[str, Any]]):
    topic = await services.get_topic(id)
    return await services.publish_messages(topic_id=topic.id, messages=data)
