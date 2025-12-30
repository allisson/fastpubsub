import time
from typing import Any
from uuid import UUID

from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, ORJSONResponse
from gunicorn.app.base import BaseApplication
from prometheus_fastapi_instrumentator import Instrumentator

from fastpubsub import models, services
from fastpubsub.config import settings
from fastpubsub.exceptions import AlreadyExistsError, NotFoundError, ServiceUnavailable
from fastpubsub.logger import get_logger

logger = get_logger(__name__)
tags_metadata = [
    {
        "name": "topics",
        "description": "Operations with topics.",
    },
    {
        "name": "subscriptions",
        "description": "Operations with subscriptions.",
    },
    {
        "name": "monitoring",
        "description": "Operations with monitoring.",
    },
]

app = FastAPI(
    title="fastpubsub",
    description="Simple pubsub system based on FastAPI and PostgreSQL.",
    debug=settings.api_debug,
    default_response_class=ORJSONResponse,
)

Instrumentator().instrument(app).expose(app)


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    logger.info(
        "request",
        extra={
            "request.client.host": request.client.host,
            "request.method": request.method,
            "request.url.path": request.url.path,
        },
    )

    response = await call_next(request)

    end_time = time.time()
    process_time = end_time - start_time
    logger.info(
        "response",
        extra={
            "request.client.host": request.client.host,
            "request.method": request.method,
            "request.url.path": request.url.path,
            "response.status_code": response.status_code,
            "time": f"{process_time:.4f}s",
        },
    )

    return response


def _create_error_response(model_class, status_code: int, exc: Exception):
    """Helper to create error responses."""
    response = jsonable_encoder(model_class(detail=exc.args[0]))
    return JSONResponse(status_code=status_code, content=response)


@app.exception_handler(AlreadyExistsError)
def already_exists_exception_handler(request: Request, exc: AlreadyExistsError):
    return _create_error_response(models.AlreadyExists, status.HTTP_409_CONFLICT, exc)


@app.exception_handler(NotFoundError)
def not_found_exception_handler(request: Request, exc: NotFoundError):
    return _create_error_response(models.NotFound, status.HTTP_404_NOT_FOUND, exc)


@app.exception_handler(ServiceUnavailable)
def service_unavailable_exception_handler(request: Request, exc: ServiceUnavailable):
    return _create_error_response(models.ServiceUnavailable, status.HTTP_503_SERVICE_UNAVAILABLE, exc)


@app.post(
    "/topics",
    response_model=models.Topic,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": models.AlreadyExists}},
    tags=["topics"],
)
async def create_topic(data: models.CreateTopic):
    return await services.create_topic(data)


@app.get(
    "/topics/{id}",
    response_model=models.Topic,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    tags=["topics"],
)
async def get_topic(id: str):
    return await services.get_topic(id)


@app.get("/topics", response_model=models.ListTopicAPI, status_code=status.HTTP_200_OK, tags=["topics"])
async def list_topic(offset: int = 0, limit: int = 10):
    topics = await services.list_topic(offset, limit)
    return models.ListTopicAPI(data=topics)


@app.delete(
    "/topics/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    tags=["topics"],
)
async def delete_topic(id: str):
    await services.delete_topic(id)


@app.post(
    "/topics/{id}/messages",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    tags=["topics"],
)
async def publish_messages(id: str, data: list[dict[str, Any]]):
    topic = await services.get_topic(id)
    return await services.publish_messages(topic_id=topic.id, messages=data)


@app.post(
    "/subscriptions",
    response_model=models.Subscription,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": models.AlreadyExists}},
    tags=["subscriptions"],
)
async def create_subscription(data: models.CreateSubscription):
    return await services.create_subscription(data)


@app.get(
    "/subscriptions/{id}",
    response_model=models.Subscription,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
async def get_subscription(id: str):
    return await services.get_subscription(id)


@app.get(
    "/subscriptions",
    response_model=models.ListSubscriptionAPI,
    status_code=status.HTTP_200_OK,
    tags=["subscriptions"],
)
async def list_subscription(offset: int = 0, limit: int = 10):
    subscriptions = await services.list_subscription(offset, limit)
    return models.ListSubscriptionAPI(data=subscriptions)


@app.delete(
    "/subscriptions/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
async def delete_subscription(id: str):
    await services.delete_subscription(id)


@app.get(
    "/subscriptions/{id}/messages",
    response_model=models.ListMessageAPI,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
async def consume_messages(id: str, consumer_id: str, batch_size: int = 10):
    subscription = await get_subscription(id)
    messages = await services.consume_messages(
        subscription_id=subscription.id, consumer_id=consumer_id, batch_size=batch_size
    )
    return models.ListMessageAPI(data=messages)


@app.post(
    "/subscriptions/{id}/acks",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
async def ack_messages(id: str, data: list[UUID]):
    subscription = await get_subscription(id)
    await services.ack_messages(subscription_id=subscription.id, message_ids=data)


@app.post(
    "/subscriptions/{id}/nacks",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
async def nack_messages(id: str, data: list[UUID]):
    subscription = await get_subscription(id)
    await services.nack_messages(subscription_id=subscription.id, message_ids=data)


@app.get(
    "/subscriptions/{id}/dlq",
    response_model=models.ListMessageAPI,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
async def list_dlq(id: str, offset: int = 0, limit: int = 10):
    subscription = await get_subscription(id)
    messages = await services.list_dlq_messages(subscription_id=subscription.id, offset=offset, limit=limit)
    return models.ListMessageAPI(data=messages)


@app.post(
    "/subscriptions/{id}/dlq/reprocess",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
async def reprocess_dlq(id: str, data: list[UUID]):
    subscription = await get_subscription(id)
    await services.reprocess_dlq_messages(subscription_id=subscription.id, message_ids=data)


@app.get(
    "/subscriptions/{id}/metrics",
    response_model=models.SubscriptionMetrics,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
async def subscription_metrics(id: str):
    subscription = await get_subscription(id)
    return await services.subscription_metrics(subscription_id=subscription.id)


@app.get("/liveness", response_model=models.HealthCheck, status_code=status.HTTP_200_OK, tags=["monitoring"])
async def liveness_probe():
    return models.HealthCheck(status="alive")


@app.get(
    "/readiness",
    response_model=models.HealthCheck,
    status_code=status.HTTP_200_OK,
    responses={503: {"model": models.ServiceUnavailable}},
    tags=["monitoring"],
)
async def readiness_probe():
    try:
        is_db_ok = await services.database_ping()
        if not is_db_ok:
            raise ServiceUnavailable("database is down")
    except Exception:
        raise ServiceUnavailable("database is down") from None

    return models.HealthCheck(status="ready")


class CustomGunicornApp(BaseApplication):
    def __init__(self, app, options=None):
        self.options = options or {}
        self.application = app
        super().__init__()

    def load_config(self):
        for key, value in self.options.items():
            if key in self.cfg.settings and value is not None:
                self.cfg.set(key, value)

    def load(self):
        return self.application


def run_server():
    options = {
        "bind": f"{settings.api_host}:{settings.api_port}",
        "workers": settings.api_num_workers,
        "loglevel": settings.log_level,
        "worker_class": "uvicorn.workers.UvicornWorker",
    }
    CustomGunicornApp(app, options).run()
