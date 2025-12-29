from fastapi import status

from fastpubsub.models import CreateSubscription, CreateTopic
from fastpubsub.services import (
    consume_messages,
    create_subscription,
    create_topic,
    nack_messages,
    publish_messages,
)


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
    create_topic(data=CreateTopic(id="my-topic"))

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
        create_topic(data=CreateTopic(id=topic_data["id"]))

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
    create_topic(data=CreateTopic(id="my-topic"))

    response = client.delete("/topics/my-topic")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.delete("/topics/my-topic")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Topic not found"}


def test_publish_messages(session, client):
    create_topic(data=CreateTopic(id="my-topic"))

    data = [{"id": 1}, {"id": 2}]

    response = client.post("/topics/my-topic/messages", json=data)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.post("/topics/not-found-topic/messages", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Topic not found"}


def test_create_subscription(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    data = {"id": "my-subscription", "topic_id": "my-topic"}

    response = client.post("/subscriptions", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert response_data["id"] == data["id"]
    assert response_data["topic_id"] == data["topic_id"]

    response = client.post("/subscriptions", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_409_CONFLICT
    assert response_data == {"detail": "This subscription already exists"}


def test_get_subscription(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    create_subscription(data=CreateSubscription(id="my-subscription", topic_id="my-topic"))

    response = client.get("/subscriptions/my-subscription")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data["id"] == "my-subscription"
    assert response_data["topic_id"] == "my-topic"
    assert response_data["created_at"]

    response = client.get("/subscriptions/my-subscription-x")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_list_subscription(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    data = [{"id": "my-subscription-1"}, {"id": "my-subscription-2"}]
    for subscription_data in data:
        create_subscription(data=CreateSubscription(id=subscription_data["id"], topic_id="my-topic"))

    response = client.get("/subscriptions")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 2
    assert response_data["data"][0]["id"] == "my-subscription-1"
    assert response_data["data"][1]["id"] == "my-subscription-2"

    response = client.get("/subscriptions", params={"offset": 0, "limit": 1})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == "my-subscription-1"

    response = client.get("/subscriptions", params={"offset": 1, "limit": 1})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["id"] == "my-subscription-2"


def test_delete_subscription(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    create_subscription(data=CreateSubscription(id="my-subscription", topic_id="my-topic"))

    response = client.delete("/subscriptions/my-subscription")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.delete("/subscriptions/my-subscription")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_consume_messages(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    create_subscription(data=CreateSubscription(id="my-subscription", topic_id="my-topic"))
    publish_messages(topic_id="my-topic", messages=[{"id": 1}])

    response = client.get(
        "/subscriptions/my-subscription/messages", params={"consumer_id": "id", "batch_size": 1}
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["subscription_id"] == "my-subscription"

    response = client.get(
        "/subscriptions/not-found-subscription/messages", params={"consumer_id": "id", "batch_size": 1}
    )
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_ack_messages(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    create_subscription(data=CreateSubscription(id="my-subscription", topic_id="my-topic"))
    publish_messages(topic_id="my-topic", messages=[{"id": 1}])
    messages = consume_messages(subscription_id="my-subscription", consumer_id="id", batch_size=1)
    data = [str(message.id) for message in messages]

    response = client.post("/subscriptions/my-subscription/acks", json=data)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.post("/subscriptions/not-found-subscription/acks", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_nack_messages(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    create_subscription(data=CreateSubscription(id="my-subscription", topic_id="my-topic"))
    publish_messages(topic_id="my-topic", messages=[{"id": 1}])
    messages = consume_messages(subscription_id="my-subscription", consumer_id="id", batch_size=1)
    data = [str(message.id) for message in messages]

    response = client.post("/subscriptions/my-subscription/nacks", json=data)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.post("/subscriptions/not-found-subscription/nacks", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_list_dlq(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    create_subscription(
        data=CreateSubscription(id="my-subscription", topic_id="my-topic", max_delivery_attempts=1)
    )
    publish_messages(topic_id="my-topic", messages=[{"id": 1}])
    messages = consume_messages(subscription_id="my-subscription", consumer_id="id", batch_size=1)
    nack_messages(subscription_id="my-subscription", message_ids=[str(message.id) for message in messages])

    response = client.get("/subscriptions/my-subscription/dlq", params={"offset": 0, "limit": 1})
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert len(response_data["data"]) == 1
    assert response_data["data"][0]["subscription_id"] == "my-subscription"

    response = client.get("/subscriptions/not-found-subscription/dlq", params={"offset": 0, "limit": 1})
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_reprocess_dlq(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    create_subscription(
        data=CreateSubscription(id="my-subscription", topic_id="my-topic", max_delivery_attempts=1)
    )
    publish_messages(topic_id="my-topic", messages=[{"id": 1}])
    messages = consume_messages(subscription_id="my-subscription", consumer_id="id", batch_size=1)
    message = messages[0]
    nack_messages(subscription_id="my-subscription", message_ids=[str(message.id)])
    data = [str(message.id)]

    response = client.post("/subscriptions/my-subscription/dlq/reprocess", json=data)
    messages = consume_messages(subscription_id="my-subscription", consumer_id="id", batch_size=1)

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(messages) == 1
    assert messages[0] == message

    response = client.post("/subscriptions/not-found-subscription/dlq/reprocess", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_subscription_metrics(session, client):
    create_topic(data=CreateTopic(id="my-topic"))
    create_subscription(data=CreateSubscription(id="my-subscription", topic_id="my-topic"))

    response = client.get("/subscriptions/my-subscription/metrics")
    response_data = response.json()

    assert response.status_code == status.HTTP_200_OK
    assert response_data == {
        "acked": 0,
        "available": 0,
        "delivered": 0,
        "dlq": 0,
        "subscription_id": "my-subscription",
    }

    response = client.get("/subscriptions/not-found-subscription/metrics")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}
