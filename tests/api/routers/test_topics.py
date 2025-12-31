from fastapi import status

from fastpubsub.models import CreateTopic
from fastpubsub.services import create_topic
from tests.helpers import sync_call_service


def test_create_topic(session, client):
    data = {"id": "my-topic"}

    response = client.post("/topics", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert response_data["id"] == data["id"]

    response = client.post("/topics", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response_data == {"detail": "This topic already exists"}


def test_get_topic(session, client):
    sync_call_service(create_topic, data=CreateTopic(id="my-topic"))

    response = client.get("/topics/my-topic")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == "my-topic"
    assert response_data["created_at"]

    response = client.get("/topics/my-topic-x")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Topic not found"}


def test_list_topic(session, client):
    data = [{"id": "my-topic-1"}, {"id": "my-topic-2"}]
    for topic_data in data:
        sync_call_service(create_topic, data=CreateTopic(id=topic_data["id"]))

    response = client.get("/topics")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 2
    assert response_data["data"][0]["id"] == "my-topic-1"
    assert response_data["data"][1]["id"] == "my-topic-2"

    response = client.get("/topics", params={"offset": 0, "limit": 1})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == "my-topic-1"

    response = client.get("/topics", params={"offset": 1, "limit": 1})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == "my-topic-2"


def test_delete_topic(session, client):
    sync_call_service(create_topic, data=CreateTopic(id="my-topic"))

    response = client.delete("/topics/my-topic")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.delete("/topics/my-topic")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Topic not found"}


def test_publish_messages(session, client):
    sync_call_service(create_topic, data=CreateTopic(id="my-topic"))

    data = [{"id": 1}, {"id": 2}]

    response = client.post("/topics/my-topic/messages", json=data)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.post("/topics/not-found-topic/messages", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Topic not found"}
