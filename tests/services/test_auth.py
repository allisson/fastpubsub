from typing import Annotated

import pytest
import pytest_asyncio
from fastapi import Depends, FastAPI, Request, status
from fastapi.testclient import TestClient

from fastpubsub import models, services
from fastpubsub.api.helpers import _create_error_response
from fastpubsub.config import settings
from fastpubsub.exceptions import InvalidClient, InvalidClientToken
from fastpubsub.models import DecodedClientToken
from tests.helpers import sync_call_function


@pytest_asyncio.fixture
async def make_client_token():
    async def _make_token(scopes: list[str], is_active: bool = True) -> models.ClientToken:
        client_result = await services.create_client(
            data=models.CreateClient(name="client", scopes=" ".join(scopes), is_active=is_active)
        )
        return await services.issue_jwt_client_token(client_result.id, client_result.secret)

    return _make_token


@pytest.fixture
def app():
    app = FastAPI()

    @app.get("/topics/{id}")
    def read_topic(
        id: str,
        token: Annotated[DecodedClientToken, Depends(services.require_scope("topics", "read"))],
    ):
        return {"topic": id}

    @app.exception_handler(InvalidClient)
    def invalid_client_exception_handler(request: Request, exc: InvalidClient):
        return _create_error_response(models.GenericError, status.HTTP_401_UNAUTHORIZED, exc)

    @app.exception_handler(InvalidClientToken)
    def invalid_client_token_exception_handler(request: Request, exc: InvalidClientToken):
        return _create_error_response(models.GenericError, status.HTTP_403_FORBIDDEN, exc)

    return app


@pytest.mark.parametrize(
    "scopes,resource,action,resource_id,expected_result",
    [
        ({"topics:publish"}, "topics", "publish", None, True),
        ({"topics:publish"}, "topics", "publish", "topic", True),
        ({"topics:publish:my-topic"}, "topics", "publish", "my-topic", True),
        ({"topics:publish:my-topic"}, "topics", "publish", "other-topic", False),
        ({"topics:publish:my-topic"}, "topics", "publish", None, False),
        ({"topics:read"}, "topics", "publish", "topic", False),
        ({"topics:read"}, "topics", "publish", None, False),
        ({"*"}, "topics", "publish", None, True),
        ({"*"}, "topics", "publish", "topic", True),
        ({"*"}, "topics", "publish", "my-topic", True),
        ({"*"}, "topics", "publish", "other-topic", True),
        ({"*"}, "topics", "publish", None, True),
        ({"*"}, "topics", "publish", "topic", True),
        ({"*"}, "topics", "publish", None, True),
    ],
)
def test_has_scope(scopes, resource, action, resource_id, expected_result):
    assert services.has_scope(scopes, resource, action, resource_id) == expected_result


def test_require_scope(app, make_client_token, monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    client = TestClient(app)
    client_token = sync_call_function(make_client_token, scopes=["topics:read:my-topic"])
    headers = {"Authorization": f"Bearer {client_token.access_token}"}
    sync_call_function(services.create_topic, data=models.CreateTopic(id="my-topic"))

    response = client.get("/topics/my-topic")
    response_data = response.json()

    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert response_data == {"detail": "Invalid jwt token"}

    response = client.get("/topics/my-topic", headers=headers)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data == {"topic": "my-topic"}

    response = client.get("/topics/my-topic-x", headers=headers)
    response_data = response.json()

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert response_data == {"detail": "Insufficient scope"}
