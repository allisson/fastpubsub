from fastapi import status


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
    data = {"id": "my-topic"}

    client.post("/topics", json=data)

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
        client.post("/topics", json=topic_data)

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
    data = {"id": "my-topic"}

    client.post("/topics", json=data)

    response = client.delete("/topics/my-topic")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.delete("/topics/my-topic")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Topic not found"}
