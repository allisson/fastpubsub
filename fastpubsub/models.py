import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from fastpubsub.config import settings

regex_for_id = "^[a-zA-Z0-9-._]+$"


class NotFound(BaseModel):
    detail: str


class AlreadyExists(BaseModel):
    detail: str


class ServiceUnavailable(BaseModel):
    detail: str


class CreateTopic(BaseModel):
    id: str = Field(..., pattern=regex_for_id, max_length=128)


class Topic(BaseModel):
    id: str
    created_at: datetime


class ListTopicAPI(BaseModel):
    data: list[Topic]


class CreateSubscription(BaseModel):
    id: str = Field(..., pattern=regex_for_id, max_length=128)
    topic_id: str = Field(..., pattern=regex_for_id, max_length=128)
    filter: dict | None = None
    max_delivery_attempts: int = Field(default=settings.subscription_max_attempts, ge=1)
    backoff_min_seconds: int = Field(default=settings.subscription_backoff_min_seconds, ge=1)
    backoff_max_seconds: int = Field(default=settings.subscription_backoff_max_seconds, ge=1)


class Subscription(BaseModel):
    id: str
    topic_id: str
    filter: dict | None
    max_delivery_attempts: int
    backoff_min_seconds: int
    backoff_max_seconds: int
    created_at: datetime


class ListSubscriptionAPI(BaseModel):
    data: list[Subscription]


class Message(BaseModel):
    id: uuid.UUID
    subscription_id: str
    payload: dict
    delivery_attempts: int
    created_at: datetime


class ListMessageAPI(BaseModel):
    data: list[Message]


class SubscriptionMetrics(BaseModel):
    subscription_id: str
    available: int
    delivered: int
    acked: int
    dlq: int


class HealthCheck(BaseModel):
    status: str
