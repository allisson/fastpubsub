import pytest
from pydantic import ValidationError

from fastpubsub.models import CreateClient


@pytest.mark.parametrize(
    "scopes",
    [
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
    ],
)
def test_create_client_with_valid_scopes(scopes):
    client = CreateClient(name="my client", scopes=scopes)

    assert client.scopes == scopes


@pytest.mark.parametrize(
    "scopes",
    [
        "",
        "topic:create",
        "topic:read",
        "topic:delete",
        "topic:publish",
        "subscription:create",
        "subscription:read",
        "subscription:delete",
        "subscription:consume",
        "client:create",
        "client:update",
        "client:read",
        "client:delete",
    ],
)
def test_create_client_with_invalid_scopes(scopes):
    print(f"scopes={scopes}")
    with pytest.raises(ValidationError):
        CreateClient(name="my client", scopes=scopes)
