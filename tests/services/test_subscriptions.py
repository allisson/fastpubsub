import pytest

from fastpubsub import services
from fastpubsub.exceptions import AlreadyExistsError, NotFoundError
from fastpubsub.models import CreateSubscription, CreateTopic


@pytest.mark.asyncio
async def test_create_and_get_subscription(session):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    data = CreateSubscription(
        id=subscription_id,
        topic_id=topic_id,
        filter={"field": ["value"]},
        max_delivery_attempts=10,
        backoff_min_seconds=60,
        backoff_max_seconds=3600,
    )

    topic = await services.create_topic(data=CreateTopic(id=topic_id))
    subscription = await services.create_subscription(data=data)

    assert subscription.id == subscription_id
    assert subscription.topic_id == topic.id
    assert subscription.filter == {"field": ["value"]}
    assert subscription.max_delivery_attempts == 10
    assert subscription.backoff_min_seconds == 60
    assert subscription.backoff_max_seconds == 3600
    assert subscription.created_at is not None
    assert subscription == await services.get_subscription(subscription_id)

    with pytest.raises(NotFoundError) as excinfo:
        await services.get_subscription("not-found-subscription")
    assert "Subscription not found" in str(excinfo.value)

    with pytest.raises(AlreadyExistsError) as excinfo:
        await services.create_subscription(data=data)
    assert "This subscription already exists" in str(excinfo.value)

    with pytest.raises(NotFoundError) as excinfo:
        await services.create_subscription(
            data=CreateSubscription(id="sub_with_not_found_topic", topic_id="not_found")
        )
    assert "Topic not found" in str(excinfo.value)


@pytest.mark.asyncio
async def test_list_subscription(session):
    topic_id = "topic"
    subscription_id_1 = "a-sub"
    subscription_id_2 = "b-sub"
    data_1 = CreateSubscription(id=subscription_id_1, topic_id=topic_id)
    data_2 = CreateSubscription(id=subscription_id_2, topic_id=topic_id)

    await services.create_topic(data=CreateTopic(id=topic_id))
    subscription_1 = await services.create_subscription(data=data_1)
    subscription_2 = await services.create_subscription(data=data_2)

    subscriptions = await services.list_subscription(offset=0, limit=1)

    assert len(subscriptions) == 1
    assert subscriptions[0] == subscription_1

    subscriptions = await services.list_subscription(offset=1, limit=1)
    assert len(subscriptions) == 1
    assert subscriptions[0] == subscription_2

    subscriptions = await services.list_subscription(offset=2, limit=1)
    assert len(subscriptions) == 0


@pytest.mark.asyncio
async def test_delete_subscription(session):
    topic_id = "my_topic"
    subscription_id = "my_sub"
    data = CreateSubscription(id=subscription_id, topic_id=topic_id)

    await services.create_topic(data=CreateTopic(id=topic_id))
    await services.create_subscription(data=data)

    await services.delete_subscription(subscription_id)

    with pytest.raises(NotFoundError) as excinfo:
        await services.get_subscription(subscription_id)
    assert "Subscription not found" in str(excinfo.value)
