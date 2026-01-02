import uuid

from fastapi import status

from fastpubsub.models import CreateClient
from fastpubsub.services import create_client
from tests.helpers import sync_call_function


def test_create_client(session, client):
    data = {"name": "my-client", "scopes": "*", "is_active": True}

    response = client.post("/clients", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert len(response_data["id"]) == 36
    assert len(response_data["secret"]) == 32


def test_get_client(session, client):
    client_result = sync_call_function(
        create_client, data=CreateClient(name="my-client", scopes="*", is_active=True)
    )

    response = client.get(f"/clients/{client_result.id}")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(client_result.id)
    assert response_data["name"] == "my-client"
    assert response_data["scopes"] == "*"
    assert response_data["is_active"] is True
    assert response_data["token_version"] == 1
    assert response_data["created_at"]
    assert response_data["updated_at"]

    response = client.get(f"/clients/{uuid.uuid7()}")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Client not found"}


def test_update_client(session, client):
    client_result = sync_call_function(
        create_client, data=CreateClient(name="my-client", scopes="*", is_active=True)
    )
    data = {"name": "my-updated-client", "scopes": "clients:update", "is_active": False}

    response = client.put(f"/clients/{client_result.id}", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == str(client_result.id)
    assert response_data["name"] == "my-updated-client"
    assert response_data["scopes"] == "clients:update"
    assert response_data["is_active"] is False
    assert response_data["token_version"] == 2
    assert response_data["created_at"]
    assert response_data["updated_at"]

    response = client.put(f"/clients/{uuid.uuid7()}", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Client not found"}


def test_list_client(session, client):
    client_result_1 = sync_call_function(create_client, data=CreateClient(name="my-client-1", scopes="*"))
    client_result_2 = sync_call_function(create_client, data=CreateClient(name="my-client-2", scopes="*"))

    response = client.get("/clients")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 2
    assert response_data["data"][0]["id"] == str(client_result_1.id)
    assert response_data["data"][1]["id"] == str(client_result_2.id)

    response = client.get("/clients", params={"offset": 0, "limit": 1})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == str(client_result_1.id)

    response = client.get("/clients", params={"offset": 1, "limit": 1})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == str(client_result_2.id)


def test_delete_client(session, client):
    client_result = sync_call_function(create_client, data=CreateClient(name="my-client", scopes="*"))

    response = client.delete(f"/clients/{client_result.id}")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.delete(f"/clients/{client_result.id}")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Client not found"}


def test_issue_client_token(session, client):
    client_result = sync_call_function(create_client, data=CreateClient(name="my-client", scopes="*"))
    data = {"client_id": str(client_result.id), "client_secret": client_result.secret}

    response = client.post("/oauth/token", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert response_data["access_token"]
    assert response_data["token_type"] == "Bearer"
    assert response_data["expires_in"] == 1800
    assert response_data["scope"] == "*"
