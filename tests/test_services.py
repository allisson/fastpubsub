import time

import pytest

from fastpubsub import services
from fastpubsub.database import SubscriptionMessage as DBSubscriptionMessage
from fastpubsub.exceptions import AlreadyExistsError, NotFoundError
from fastpubsub.models import CreateSubscription, CreateTopic, SubscriptionMetrics


@pytest.fixture
def messages():
    return [{"country": "BR"}, {"country": "US"}, {"country": "DE"}]


def get_db_messages(session, subscription_id):
    return session.query(DBSubscriptionMessage).filter_by(subscription_id=subscription_id).all()


def test_create_and_get_topic(session):
    topic_id = "my_topic"
    topic = services.create_topic(data=CreateTopic(id=topic_id))

    assert topic.id == topic_id
    assert topic.created_at is not None
    assert topic == services.get_topic(topic_id)

    with pytest.raises(NotFoundError) as excinfo:
        services.get_topic("not-found-topic")
    assert "Topic not found" in str(excinfo.value)

    with pytest.raises(AlreadyExistsError) as excinfo:
        services.create_topic(data=CreateTopic(id=topic_id))
    assert "This topic already exists" in str(excinfo.value)


def test_list_topic(session):
    topic_id_1 = "a-topic"
    topic_id_2 = "b-topic"
    topic_1 = services.create_topic(data=CreateTopic(id=topic_id_1))
    topic_2 = services.create_topic(data=CreateTopic(id=topic_id_2))

    topics = services.list_topic(offset=0, limit=1)

    assert len(topics) == 1
    assert topics[0] == topic_1

    topics = services.list_topic(offset=1, limit=1)
    assert len(topics) == 1
    assert topics[0] == topic_2

    topics = services.list_topic(offset=2, limit=1)
    assert len(topics) == 0


def test_delete_topic(session):
    topic_id = "my_topic"
    services.create_topic(data=CreateTopic(id=topic_id))

    services.delete_topic(topic_id)

    with pytest.raises(NotFoundError) as excinfo:
        services.get_topic(topic_id)
    assert "Topic not found" in str(excinfo.value)


def test_create_and_get_subscription(session):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    data = CreateSubscription(
        id=subscription_id,
        topic_id=topic_id,
        filter={"field": "value"},
        max_delivery_attempts=10,
        backoff_min_seconds=60,
        backoff_max_seconds=3600,
    )

    topic = services.create_topic(data=CreateTopic(id=topic_id))
    subscription = services.create_subscription(data=data)

    assert subscription.id == subscription_id
    assert subscription.topic_id == topic.id
    assert subscription.filter == {"field": "value"}
    assert subscription.max_delivery_attempts == 10
    assert subscription.backoff_min_seconds == 60
    assert subscription.backoff_max_seconds == 3600
    assert subscription.created_at is not None
    assert subscription == services.get_subscription(subscription_id)

    with pytest.raises(NotFoundError) as excinfo:
        services.get_subscription("not-found-subscription")
    assert "Subscription not found" in str(excinfo.value)

    with pytest.raises(AlreadyExistsError) as excinfo:
        services.create_subscription(data=data)
    assert "This subscription already exists" in str(excinfo.value)

    with pytest.raises(NotFoundError) as excinfo:
        services.create_subscription(
            data=CreateSubscription(id="sub_with_not_found_topic", topic_id="not_found")
        )
    assert "Topic not found" in str(excinfo.value)


def test_list_subscription(session):
    topic_id = "topic"
    subscription_id_1 = "a-sub"
    subscription_id_2 = "b-sub"
    data_1 = CreateSubscription(id=subscription_id_1, topic_id=topic_id)
    data_2 = CreateSubscription(id=subscription_id_2, topic_id=topic_id)

    services.create_topic(data=CreateTopic(id=topic_id))
    subscription_1 = services.create_subscription(data=data_1)
    subscription_2 = services.create_subscription(data=data_2)

    subscriptions = services.list_subscription(offset=0, limit=1)

    assert len(subscriptions) == 1
    assert subscriptions[0] == subscription_1

    subscriptions = services.list_subscription(offset=1, limit=1)
    assert len(subscriptions) == 1
    assert subscriptions[0] == subscription_2

    subscriptions = services.list_subscription(offset=2, limit=1)
    assert len(subscriptions) == 0


def test_delete_subscription(session):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    data = CreateSubscription(id=subscription_id, topic_id=topic_id)

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(data=data)

    services.delete_subscription(subscription_id)

    with pytest.raises(NotFoundError) as excinfo:
        services.get_subscription(subscription_id)
    assert "Subscription not found" in str(excinfo.value)


def test_publish_and_consume_messages_with_one_subscription(session, messages):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(data=CreateSubscription(id=subscription_id, topic_id=topic_id))

    result = services.publish_messages(topic_id, messages)
    assert result == 3

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3

    result = services.ack_messages(subscription_id, [message.id for message in messages])
    assert result is True

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 0


def test_publish_and_consume_messages_with_multiple_subscription(session, messages):
    topic_id = "my_topic"
    subscription_id_1 = "my_sub_1"
    subscription_id_2 = "my_sub_2"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(data=CreateSubscription(id=subscription_id_1, topic_id=topic_id))
    services.create_subscription(data=CreateSubscription(id=subscription_id_2, topic_id=topic_id))

    result = services.publish_messages(topic_id, messages)
    assert result == 6

    messages = services.consume_messages(subscription_id_1, consumer_id, 10)
    assert len(messages) == 3

    result = services.ack_messages(subscription_id_1, [message.id for message in messages])
    assert result is True

    messages = services.consume_messages(subscription_id_1, consumer_id, 10)
    assert len(messages) == 0

    messages = services.consume_messages(subscription_id_2, consumer_id, 10)
    assert len(messages) == 3

    result = services.ack_messages(subscription_id_2, [message.id for message in messages])
    assert result is True

    messages = services.consume_messages(subscription_id_2, consumer_id, 10)
    assert len(messages) == 0


@pytest.mark.parametrize(
    "filter, expected_messages",
    [
        ({}, 3),
        (None, 3),
        ({"country": "BR"}, 3),  # invalid filter format
        ({"other_field": ["other_value"]}, 3),
        ({"country": ["BR"]}, 1),
        ({"country": ["BR", "PL"]}, 1),
        ({"country": ["BR", "PL", "DE"]}, 2),
        ({"country": ["BR", "PL", "DE", "US"]}, 3),
    ],
)
def test_publish_and_consume_messages_with_filter(session, filter, expected_messages, messages):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(
        data=CreateSubscription(id=subscription_id, topic_id=topic_id, filter=filter)
    )

    result = services.publish_messages(topic_id, messages)
    assert result == expected_messages

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == expected_messages


def test_publish_and_consume_messages_with_multiple_subscription_and_filter(session, messages):
    topic_id = "my_topic"
    subscription_id_1 = "my_sub_1"
    subscription_id_2 = "my_sub_2"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(data=CreateSubscription(id=subscription_id_1, topic_id=topic_id))
    services.create_subscription(
        data=CreateSubscription(id=subscription_id_2, topic_id=topic_id, filter={"country": ["BR"]})
    )

    result = services.publish_messages(topic_id, messages)
    assert result == 4

    messages = services.consume_messages(subscription_id_1, consumer_id, 10)
    assert len(messages) == 3

    result = services.ack_messages(subscription_id_1, [message.id for message in messages])
    assert result is True

    messages = services.consume_messages(subscription_id_1, consumer_id, 10)
    assert len(messages) == 0

    messages = services.consume_messages(subscription_id_2, consumer_id, 10)
    assert len(messages) == 1

    result = services.ack_messages(subscription_id_2, [message.id for message in messages])
    assert result is True

    messages = services.consume_messages(subscription_id_2, consumer_id, 10)
    assert len(messages) == 0


def test_nack(session, messages):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(
        data=CreateSubscription(
            id=subscription_id, topic_id=topic_id, backoff_min_seconds=1, backoff_max_seconds=1
        )
    )

    result = services.publish_messages(topic_id, messages)
    assert result == 3

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3

    result = services.nack_messages(subscription_id, [message.id for message in messages])
    assert result is True

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 0

    time.sleep(1)

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3


def test_nack_going_to_dlq(session, messages):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(
        data=CreateSubscription(id=subscription_id, topic_id=topic_id, max_delivery_attempts=1)
    )

    result = services.publish_messages(topic_id, messages)
    assert result == 3

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3

    result = services.nack_messages(subscription_id, [message.id for message in messages])
    assert result is True

    messages = services.list_dlq_messages(subscription_id, 0, 10)
    assert len(messages) == 3


def test_reprocess_dlq_messages(session, messages):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(
        data=CreateSubscription(id=subscription_id, topic_id=topic_id, max_delivery_attempts=1)
    )

    result = services.publish_messages(topic_id, messages)
    assert result == 3

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3

    result = services.nack_messages(subscription_id, [message.id for message in messages])
    assert result is True

    messages = services.list_dlq_messages(subscription_id, 0, 10)
    assert len(messages) == 3

    result = services.reprocess_dlq_messages(subscription_id, [message.id for message in messages])
    assert result is True

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3


def test_cleanup_stuck_messages(session, messages):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(data=CreateSubscription(id=subscription_id, topic_id=topic_id))

    result = services.publish_messages(topic_id, messages)
    assert result == 3

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 0

    time.sleep(1)

    result = services.cleanup_stuck_messages(1)
    assert result is True

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3


def test_cleanup_acked_messages(session, messages):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    consumer_id = "consumer_id"

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(data=CreateSubscription(id=subscription_id, topic_id=topic_id))

    result = services.publish_messages(topic_id, messages)
    assert result == 3

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 3

    result = services.ack_messages(subscription_id, [message.id for message in messages])
    assert result is True

    messages = services.consume_messages(subscription_id, consumer_id, 10)
    assert len(messages) == 0

    db_messages = get_db_messages(session, subscription_id)
    assert len(db_messages) == 3

    time.sleep(1)

    result = services.cleanup_acked_messages(1)
    assert result is True

    db_messages = get_db_messages(session, subscription_id)
    assert len(db_messages) == 0


def test_subscription_metrics(session):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    consumer_id = "consumer_id"
    messages = [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}]
    expected_metrics = SubscriptionMetrics(
        subscription_id=subscription_id, available=1, delivered=1, acked=1, dlq=1
    )

    services.create_topic(data=CreateTopic(id=topic_id))
    services.create_subscription(
        data=CreateSubscription(id=subscription_id, topic_id=topic_id, max_delivery_attempts=1)
    )

    result = services.publish_messages(topic_id, messages)
    assert result == 4

    messages = services.consume_messages(subscription_id, consumer_id, 3)
    assert len(messages) == 3

    result = services.ack_messages(subscription_id, [messages[0].id])
    assert result is True

    result = services.nack_messages(subscription_id, [messages[1].id])
    assert result is True

    metrics = services.subscription_metrics(subscription_id)
    assert metrics == expected_metrics


def test_database_ping(session):
    assert services.database_ping() is True
