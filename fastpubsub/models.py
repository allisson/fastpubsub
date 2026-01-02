import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, StringConstraints

from fastpubsub.config import settings
from fastpubsub.sanitizer import sanitize_filter

regex_for_id = "^[a-zA-Z0-9-._]+$"


class GenericError(BaseModel):
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

    @field_validator("filter")
    @classmethod
    def sanitize_filter_field(cls, v):
        """Sanitize filter to prevent SQL and XSS injection attacks."""
        return sanitize_filter(v)


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


class CreateClient(BaseModel):
    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    scopes: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    is_active: bool = True

    @field_validator("scopes")
    def validate_scopes(cls, v: str):
        valid_scopes = (
            "*",
            "topics:create",
            "topics:read",
            "topics:delete",
            "topics:publish",
            "subscriptions:create",
            "subscriptions:read",
            "subscriptions:delete",
            "subscriptions:consume",
            "clients:create",
            "clients:update",
            "clients:read",
            "clients:delete",
        )
        for scope in v.split():
            base_scope = scope
            if len(scope.split(":")) == 3:
                base_scope = scope.rsplit(":", 1)[0]
            if base_scope not in valid_scopes:
                raise ValueError(f"Invalid scope {scope}")
        return v


class CreateClientResult(BaseModel):
    id: uuid.UUID
    secret: str


class Client(BaseModel):
    id: uuid.UUID
    name: str
    scopes: str
    is_active: bool
    token_version: int
    created_at: datetime
    updated_at: datetime


class UpdateClient(CreateClient):
    pass


class ClientToken(BaseModel):
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str


class DecodedClientToken(BaseModel):
    client_id: uuid.UUID
    scopes: set[str]


class ListClientAPI(BaseModel):
    data: list[Client]


class IssueClientToken(BaseModel):
    client_id: uuid.UUID
    client_secret: str
