import pytest

from fastpubsub import services
from fastpubsub.exceptions import AlreadyExistsError, NotFoundError
from fastpubsub.models import CreateTopic


@pytest.mark.asyncio
async def test_create_and_get_topic(session):
    topic_id = "my_topic"
    topic = await services.create_topic(data=CreateTopic(id=topic_id))

    assert topic.id == topic_id
    assert topic.created_at is not None
    assert topic == await services.get_topic(topic_id)

    with pytest.raises(NotFoundError) as excinfo:
        await services.get_topic("not-found-topic")
    assert "Topic not found" in str(excinfo.value)

    with pytest.raises(AlreadyExistsError) as excinfo:
        await services.create_topic(data=CreateTopic(id=topic_id))
    assert "This topic already exists" in str(excinfo.value)


@pytest.mark.asyncio
async def test_list_topic(session):
    topic_id_1 = "a-topic"
    topic_id_2 = "b-topic"
    topic_1 = await services.create_topic(data=CreateTopic(id=topic_id_1))
    topic_2 = await services.create_topic(data=CreateTopic(id=topic_id_2))

    topics = await services.list_topic(offset=0, limit=1)

    assert len(topics) == 1
    assert topics[0] == topic_1

    topics = await services.list_topic(offset=1, limit=1)
    assert len(topics) == 1
    assert topics[0] == topic_2

    topics = await services.list_topic(offset=2, limit=1)
    assert len(topics) == 0


@pytest.mark.asyncio
async def test_delete_topic(session):
    topic_id = "my_topic"
    await services.create_topic(data=CreateTopic(id=topic_id))

    await services.delete_topic(topic_id)

    with pytest.raises(NotFoundError) as excinfo:
        await services.get_topic(topic_id)
    assert "Topic not found" in str(excinfo.value)
