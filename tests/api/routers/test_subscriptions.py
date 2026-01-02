from fastapi import status

from fastpubsub.models import CreateSubscription, CreateTopic
from fastpubsub.services import (
    consume_messages,
    create_subscription,
    create_topic,
    nack_messages,
    publish_messages,
)
from tests.helpers import sync_call_function


def test_create_subscription(session, client):
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
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
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    sync_call_function(
        create_subscription, data=CreateSubscription(id="my-subscription", topic_id="my-topic")
    )

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
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    data = [{"id": "my-subscription-1"}, {"id": "my-subscription-2"}]
    for subscription_data in data:
        sync_call_function(
            create_subscription, data=CreateSubscription(id=subscription_data["id"], topic_id="my-topic")
        )

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
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    sync_call_function(
        create_subscription, data=CreateSubscription(id="my-subscription", topic_id="my-topic")
    )

    response = client.delete("/subscriptions/my-subscription")

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.delete("/subscriptions/my-subscription")
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_consume_messages(session, client):
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    sync_call_function(
        create_subscription, data=CreateSubscription(id="my-subscription", topic_id="my-topic")
    )
    sync_call_function(publish_messages, topic_id="my-topic", messages=[{"id": 1}])

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
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    sync_call_function(
        create_subscription, data=CreateSubscription(id="my-subscription", topic_id="my-topic")
    )
    sync_call_function(publish_messages, topic_id="my-topic", messages=[{"id": 1}])
    messages = sync_call_function(
        consume_messages, subscription_id="my-subscription", consumer_id="id", batch_size=1
    )
    data = [str(message.id) for message in messages]

    response = client.post("/subscriptions/my-subscription/acks", json=data)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.post("/subscriptions/not-found-subscription/acks", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_nack_messages(session, client):
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    sync_call_function(
        create_subscription, data=CreateSubscription(id="my-subscription", topic_id="my-topic")
    )
    sync_call_function(publish_messages, topic_id="my-topic", messages=[{"id": 1}])
    messages = sync_call_function(
        consume_messages, subscription_id="my-subscription", consumer_id="id", batch_size=1
    )
    data = [str(message.id) for message in messages]

    response = client.post("/subscriptions/my-subscription/nacks", json=data)

    assert response.status_code == status.HTTP_204_NO_CONTENT

    response = client.post("/subscriptions/not-found-subscription/nacks", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_list_dlq(session, client):
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    sync_call_function(
        create_subscription,
        data=CreateSubscription(id="my-subscription", topic_id="my-topic", max_delivery_attempts=1),
    )
    sync_call_function(publish_messages, topic_id="my-topic", messages=[{"id": 1}])
    messages = sync_call_function(
        consume_messages, subscription_id="my-subscription", consumer_id="id", batch_size=1
    )
    sync_call_function(
        nack_messages,
        subscription_id="my-subscription",
        message_ids=[str(message.id) for message in messages],
    )

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
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    sync_call_function(
        create_subscription,
        data=CreateSubscription(id="my-subscription", topic_id="my-topic", max_delivery_attempts=1),
    )
    sync_call_function(publish_messages, topic_id="my-topic", messages=[{"id": 1}])
    messages = sync_call_function(
        consume_messages, subscription_id="my-subscription", consumer_id="id", batch_size=1
    )
    message = messages[0]
    sync_call_function(nack_messages, subscription_id="my-subscription", message_ids=[str(message.id)])
    data = [str(message.id)]

    response = client.post("/subscriptions/my-subscription/dlq/reprocess", json=data)
    messages = sync_call_function(
        consume_messages, subscription_id="my-subscription", consumer_id="id", batch_size=1
    )

    assert response.status_code == status.HTTP_204_NO_CONTENT
    assert len(messages) == 1
    assert messages[0] == message

    response = client.post("/subscriptions/not-found-subscription/dlq/reprocess", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response_data == {"detail": "Subscription not found"}


def test_subscription_metrics(session, client):
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))
    sync_call_function(
        create_subscription, data=CreateSubscription(id="my-subscription", topic_id="my-topic")
    )

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


def test_subscription_filter_xss_sanitization(session, client):
    """Test that XSS attacks in subscription filters are sanitized."""
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))

    # Test XSS in filter value
    data = {
        "id": "xss-test-subscription",
        "topic_id": "my-topic",
        "filter": {"field": ["<script>alert('xss')</script>", "normal_value"]},
    }

    response = client.post("/subscriptions", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    assert response_data["id"] == data["id"]
    # Verify XSS is sanitized
    assert "<script>" not in str(response_data["filter"])
    assert "&lt;script&gt;" in response_data["filter"]["field"][0]
    assert "normal_value" in response_data["filter"]["field"]


def test_subscription_filter_sql_injection_patterns(session, client):
    """Test that SQL injection patterns in filters are sanitized."""
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))

    # Test SQL-like patterns in filter value
    data = {
        "id": "sql-test-subscription",
        "topic_id": "my-topic",
        "filter": {"field": ["'; DROP TABLE users; --", "1' OR '1'='1"]},
    }

    response = client.post("/subscriptions", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    # Quotes should be HTML-encoded
    assert "&#x27;" in response_data["filter"]["field"][0]
    assert "&#x27;" in response_data["filter"]["field"][1]


def test_subscription_filter_control_characters(session, client):
    """Test that control characters in filters are removed."""
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))

    # Test control characters in filter value
    data = {
        "id": "control-test-subscription",
        "topic_id": "my-topic",
        "filter": {"field": ["test\x00data", "clean"]},
    }

    response = client.post("/subscriptions", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    # Null byte should be removed
    assert "\x00" not in response_data["filter"]["field"][0]
    assert response_data["filter"]["field"][0] == "testdata"


def test_subscription_filter_invalid_structure(session, client):
    """Test that invalid filter structure is rejected."""
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))

    # Test invalid structure (value not an array)
    data = {
        "id": "invalid-subscription",
        "topic_id": "my-topic",
        "filter": {"field": "not_an_array"},  # Invalid
    }

    response = client.post("/subscriptions", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    assert "Invalid filter structure" in str(response_data)


def test_subscription_filter_with_special_characters(session, client):
    """Test that special characters are properly encoded."""
    sync_call_function(create_topic, data=CreateTopic(id="my-topic"))

    data = {
        "id": "special-chars-subscription",
        "topic_id": "my-topic",
        "filter": {"field1": ["a&b", "c<d", "e>f"], "field2": ['g"h', "i'j"]},
    }

    response = client.post("/subscriptions", json=data)
    response_data = response.json()

    assert response.status_code == status.HTTP_201_CREATED
    # Check HTML entity encoding
    assert "a&amp;b" in response_data["filter"]["field1"]
    assert any("&lt;" in val for val in response_data["filter"]["field1"])
    assert any("&gt;" in val for val in response_data["filter"]["field1"])
    assert any("&quot;" in val for val in response_data["filter"]["field2"])
    assert any("&#x27;" in val for val in response_data["filter"]["field2"])
