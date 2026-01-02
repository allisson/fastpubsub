import uuid

import pytest

from fastpubsub import services
from fastpubsub.exceptions import InvalidClient, NotFoundError
from fastpubsub.models import CreateClient, UpdateClient


@pytest.mark.asyncio
async def test_create_and_get_client(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=True)
    )

    assert isinstance(client_result.id, uuid.UUID)
    assert len(client_result.secret) == 32

    client = await services.get_client(client_result.id)

    assert client.id == client_result.id
    assert client.name == "my client"
    assert client.scopes == "*"
    assert client.is_active is True
    assert client.token_version == 1
    assert client.created_at is not None
    assert client.updated_at is not None

    with pytest.raises(NotFoundError) as excinfo:
        await services.get_client(uuid.uuid7())
    assert "Client not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_list_client(session):
    client_result_1 = await services.create_client(
        data=CreateClient(name="my client 1", scopes="*", is_active=True)
    )
    client_result_2 = await services.create_client(
        data=CreateClient(name="my client 2", scopes="*", is_active=True)
    )

    clients = await services.list_client(offset=0, limit=1)
    assert len(clients) == 1
    assert clients[0].id == client_result_1.id

    clients = await services.list_client(offset=1, limit=1)
    assert len(clients) == 1
    assert clients[0].id == client_result_2.id

    clients = await services.list_client(offset=2, limit=1)
    assert len(clients) == 0


@pytest.mark.asyncio
async def test_delete_client(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=True)
    )

    await services.delete_client(client_result.id)

    with pytest.raises(NotFoundError) as excinfo:
        await services.get_client(client_result.id)
    assert "Client not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_update_client(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=True)
    )
    client = await services.get_client(client_result.id)

    assert client.name == "my client"
    assert client.scopes == "*"
    assert client.is_active is True
    assert client.token_version == 1

    updated_client = await services.update_client(
        client.id, data=UpdateClient(name="my updated client", scopes="topics:create", is_active=False)
    )

    assert updated_client.name == "my updated client"
    assert updated_client.scopes == "topics:create"
    assert updated_client.is_active is False
    assert updated_client.token_version == 2
    assert updated_client.created_at == client.created_at
    assert updated_client.updated_at > client.updated_at

    updated_client = await services.update_client(
        client.id,
        data=UpdateClient(
            name="my new updated client", scopes="topics:create subscriptions:create", is_active=True
        ),
    )

    assert updated_client.name == "my new updated client"
    assert updated_client.scopes == "topics:create subscriptions:create"
    assert updated_client.is_active is True
    assert updated_client.token_version == 3
    assert updated_client.created_at == client.created_at
    assert updated_client.updated_at > client.updated_at


@pytest.mark.asyncio
async def test_issue_jwt_client_token_with_invalid_client_id(session):
    with pytest.raises(InvalidClient) as excinfo:
        await services.issue_jwt_client_token(client_id=uuid.uuid7(), client_secret="my-secret")
    assert "Client not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_issue_jwt_client_token_with_not_active_client(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=False)
    )

    with pytest.raises(InvalidClient) as excinfo:
        await services.issue_jwt_client_token(client_id=client_result.id, client_secret=client_result.secret)
    assert "Client disabled" in str(excinfo.value)


@pytest.mark.asyncio
async def test_issue_jwt_client_token_with_invalid_secret(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=True)
    )

    with pytest.raises(InvalidClient) as excinfo:
        await services.issue_jwt_client_token(client_id=client_result.id, client_secret="invalid-secret")
    assert "Client secret is invalid" in str(excinfo.value)


@pytest.mark.asyncio
async def test_issue_jwt_client_token(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=True)
    )

    client_token = await services.issue_jwt_client_token(
        client_id=client_result.id, client_secret=client_result.secret
    )

    assert client_token.access_token
    assert client_token.expires_in > 0
    assert client_token.scope == "*"


@pytest.mark.asyncio
async def test_decode_jwt_client_token_with_invalid_jwt_token(session):
    with pytest.raises(InvalidClient) as excinfo:
        await services.decode_jwt_client_token("invalid-jwt-token")
    assert "Invalid jwt token" in str(excinfo.value)


@pytest.mark.asyncio
async def test_decode_jwt_client_token_with_client_not_found(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=True)
    )
    client_token = await services.issue_jwt_client_token(
        client_id=client_result.id, client_secret=client_result.secret
    )
    await services.delete_client(client_result.id)

    with pytest.raises(InvalidClient) as excinfo:
        await services.decode_jwt_client_token(client_token.access_token)
    assert "Client not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_decode_jwt_client_token_with_not_active_client(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=True)
    )
    client_token = await services.issue_jwt_client_token(
        client_id=client_result.id, client_secret=client_result.secret
    )
    await services.update_client(
        client_result.id, data=UpdateClient(name="my client", scopes="*", is_active=False)
    )

    with pytest.raises(InvalidClient) as excinfo:
        await services.decode_jwt_client_token(client_token.access_token)
    assert "Client disabled" in str(excinfo.value)


@pytest.mark.asyncio
async def test_decode_jwt_client_token_with_invalid_token_version(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="*", is_active=True)
    )
    client_token = await services.issue_jwt_client_token(
        client_id=client_result.id, client_secret=client_result.secret
    )
    await services.update_client(
        client_result.id, data=UpdateClient(name="my client", scopes="*", is_active=True)
    )

    with pytest.raises(InvalidClient) as excinfo:
        await services.decode_jwt_client_token(client_token.access_token)
    assert "Token revoked" in str(excinfo.value)


@pytest.mark.asyncio
async def test_decode_jwt_client_token(session):
    client_result = await services.create_client(
        data=CreateClient(name="my client", scopes="topics:create subscriptions:create", is_active=True)
    )
    client_token = await services.issue_jwt_client_token(
        client_id=client_result.id, client_secret=client_result.secret
    )

    decoded_client = await services.decode_jwt_client_token(client_token.access_token)

    assert decoded_client.client_id == client_result.id
    assert decoded_client.scopes == set(["topics:create", "subscriptions:create"])


@pytest.mark.asyncio
async def test_decode_jwt_client_token_with_auth_disabled():
    decoded_client = await services.decode_jwt_client_token("", auth_enabled=False)

    assert isinstance(decoded_client.client_id, uuid.UUID)
    assert decoded_client.scopes == set("*")
