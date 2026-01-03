"""Pydantic models for fastpubsub API."""

import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, field_validator, StringConstraints

from fastpubsub.config import settings
from fastpubsub.sanitizer import sanitize_filter

regex_for_id = "^[a-zA-Z0-9-._]+$"


class GenericError(BaseModel):
    """Generic error response model.

    Used for consistent error responses across the API.

    Attributes:
        detail: Human-readable error message.
    """

    detail: str


class CreateTopic(BaseModel):
    """Model for creating a new topic.

    Defines the required fields for topic creation.

    Attributes:
        id: Unique identifier for the topic (alphanumeric with -._ chars, max 128 chars).
    """

    id: str = Field(..., pattern=regex_for_id, max_length=128)


class Topic(BaseModel):
    """Model representing a topic in the pub/sub system.

    Attributes:
        id: Unique identifier for the topic.
        created_at: Timestamp when the topic was created.
    """

    id: str
    created_at: datetime


class ListTopicAPI(BaseModel):
    """Model for paginated topic list response.

    Attributes:
        data: List of topic objects.
    """

    data: list[Topic]


class CreateSubscription(BaseModel):
    """Model for creating a new subscription.

    Defines the required fields for subscription creation with delivery and backoff configuration.

    Attributes:
        id: Unique identifier for the subscription (alphanumeric with -._ chars, max 128 chars).
        topic_id: ID of the topic to subscribe to.
        filter: Optional JSON filter to apply to messages.
        max_delivery_attempts: Maximum number of delivery attempts (defaults to settings).
        backoff_min_seconds: Minimum backoff time between attempts (defaults to settings).
        backoff_max_seconds: Maximum backoff time between attempts (defaults to settings).
    """

    id: str = Field(..., pattern=regex_for_id, max_length=128)
    topic_id: str = Field(..., pattern=regex_for_id, max_length=128)
    filter: dict | None = None
    max_delivery_attempts: int = Field(default=settings.subscription_max_attempts, ge=1)
    backoff_min_seconds: int = Field(default=settings.subscription_backoff_min_seconds, ge=1)
    backoff_max_seconds: int = Field(default=settings.subscription_backoff_max_seconds, ge=1)

    @field_validator("filter")
    @classmethod
    def sanitize_filter_field(cls, v):
        """Sanitize filter to prevent SQL and XSS injection attacks.

        Args:
            v: The filter dictionary to sanitize.

        Returns:
            Sanitized filter dictionary.
        """
        return sanitize_filter(v)


class Subscription(BaseModel):
    """Model representing a subscription in the pub/sub system.

    Attributes:
        id: Unique identifier for the subscription.
        topic_id: ID of the subscribed topic.
        filter: JSON filter applied to messages.
        max_delivery_attempts: Maximum delivery attempts for failed messages.
        backoff_min_seconds: Minimum backoff time between attempts.
        backoff_max_seconds: Maximum backoff time between attempts.
        created_at: Timestamp when the subscription was created.
    """

    id: str
    topic_id: str
    filter: dict | None
    max_delivery_attempts: int
    backoff_min_seconds: int
    backoff_max_seconds: int
    created_at: datetime


class ListSubscriptionAPI(BaseModel):
    """Model for paginated subscription list response.

    Attributes:
        data: List of subscription objects.
    """

    data: list[Subscription]


class Message(BaseModel):
    """Model representing a message in the pub/sub system.

    Attributes:
        id: Unique identifier for the message.
        subscription_id: ID of the subscription this message belongs to.
        payload: JSON payload of the message.
        delivery_attempts: Number of delivery attempts made.
        created_at: Timestamp when the message was created.
    """

    id: uuid.UUID
    subscription_id: str
    payload: dict
    delivery_attempts: int
    created_at: datetime


class ListMessageAPI(BaseModel):
    """Model for paginated message list response.

    Attributes:
        data: List of message objects.
    """

    data: list[Message]


class SubscriptionMetrics(BaseModel):
    """Model for subscription metrics and statistics.

    Provides counts of messages in different states for a subscription.

    Attributes:
        subscription_id: ID of the subscription.
        available: Number of messages available for consumption.
        delivered: Number of messages delivered but not yet acked.
        acked: Number of messages successfully acknowledged.
        dlq: Number of messages in dead letter queue.
    """

    subscription_id: str
    available: int
    delivered: int
    acked: int
    dlq: int


class HealthCheck(BaseModel):
    """Model for application health check response.

    Attributes:
        status: Health status string (e.g., "ok").
    """

    status: str


class CreateClient(BaseModel):
    """Model for creating a new client.

    Defines the required fields for client creation with authentication configuration.

    Attributes:
        name: Human-readable name for the client.
        scopes: Space-separated list of permissions/scopes.
        is_active: Whether the client is active and can authenticate.
    """

    name: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    scopes: Annotated[str, StringConstraints(min_length=1, strip_whitespace=True)]
    is_active: bool = True

    @field_validator("scopes")
    def validate_scopes(cls, v: str):
        """Validate that all scopes are among the allowed values.

        Args:
            v: Space-separated scopes string to validate.

        Returns:
            The validated scopes string.

        Raises:
            ValueError: If any scope is invalid.
        """
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
    """Model for client creation response.

    Contains the newly created client's ID and generated secret.

    Attributes:
        id: Unique identifier of the created client.
        secret: Generated secret key for the client.
    """

    id: uuid.UUID
    secret: str


class Client(BaseModel):
    """Model representing an authorized client.

    Attributes:
        id: Unique identifier for the client.
        name: Human-readable name for the client.
        scopes: Space-separated list of granted permissions.
        is_active: Whether the client can currently authenticate.
        token_version: Version counter for token invalidation.
        created_at: Timestamp when the client was created.
        updated_at: Timestamp when the client was last updated.
    """

    id: uuid.UUID
    name: str
    scopes: str
    is_active: bool
    token_version: int
    created_at: datetime
    updated_at: datetime


class UpdateClient(CreateClient):
    """Model for updating an existing client.

    Inherits all fields from CreateClient. Used for partial updates.
    """

    pass


class ClientToken(BaseModel):
    """Model for JWT access token response.

    Attributes:
        access_token: JWT access token string.
        token_type: Type of token (default: "Bearer").
        expires_in: Token expiration time in seconds.
        scope: Space-separated list of granted scopes.
    """

    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    scope: str


class DecodedClientToken(BaseModel):
    """Model for decoded JWT token payload.

    Attributes:
        client_id: ID of the client this token belongs to.
        scopes: Set of granted scopes from the token.
    """

    client_id: uuid.UUID
    scopes: set[str]


class ListClientAPI(BaseModel):
    """Model for paginated client list response.

    Attributes:
        data: List of client objects.
    """

    data: list[Client]


class IssueClientToken(BaseModel):
    """Model for requesting a new client token.

    Attributes:
        client_id: ID of the client requesting a token.
        client_secret: Secret key for client authentication.
    """

    client_id: uuid.UUID
    client_secret: str
