from fastapi import FastAPI, Request, status
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse, ORJSONResponse
from gunicorn.app.base import BaseApplication

from fastpubsub import models, services
from fastpubsub.config import settings
from fastpubsub.exceptions import AlreadyExistsError, NotFoundError

tags_metadata = [
    {
        "name": "topics",
        "description": "Operations with topics.",
    },
    {
        "name": "subscriptions",
        "description": "Operations with subscriptions.",
    },
]

app = FastAPI(
    title="fastpubsub",
    description="Simple pubsub system based on FastAPI and PostgreSQL.",
    debug=settings.api_debug,
    default_response_class=ORJSONResponse,
)


@app.exception_handler(AlreadyExistsError)
def already_exists_exception_handler(request: Request, exc: AlreadyExistsError):
    response = jsonable_encoder(models.AlreadyExists(detail=exc.args[0]))
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content=response)


@app.exception_handler(NotFoundError)
def not_found_exception_handler(request: Request, exc: NotFoundError):
    response = jsonable_encoder(models.NotFound(detail=exc.args[0]))
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content=response)


@app.post(
    "/topics",
    response_model=models.Topic,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": models.AlreadyExists}},
    tags=["topics"],
)
def create_topic(data: models.CreateTopic):
    return services.create_topic(data)


@app.get(
    "/topics/{id}",
    response_model=models.Topic,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    tags=["topics"],
)
def get_topic(id: str):
    return services.get_topic(id)


@app.get("/topics", response_model=models.ListTopicAPI, status_code=status.HTTP_200_OK, tags=["topics"])
def list_topic(offset: int = 0, limit: int = 10):
    topics = services.list_topic(offset, limit)
    return models.ListTopicAPI(data=topics)


@app.delete(
    "/topics/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    tags=["topics"],
)
def delete_topic(id: str):
    services.delete_topic(id)


@app.post(
    "/subscriptions",
    response_model=models.Subscription,
    status_code=status.HTTP_201_CREATED,
    responses={409: {"model": models.AlreadyExists}},
    tags=["subscriptions"],
)
def create_subscription(data: models.CreateSubscription):
    return services.create_subscription(data)


@app.get(
    "/subscriptions/{id}",
    response_model=models.Subscription,
    status_code=status.HTTP_200_OK,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
def get_subscription(id: str):
    return services.get_subscription(id)


@app.get(
    "/subscriptions",
    response_model=models.ListSubscriptionAPI,
    status_code=status.HTTP_200_OK,
    tags=["subscriptions"],
)
def list_subscription(offset: int = 0, limit: int = 10):
    subscriptions = services.list_subscription(offset, limit)
    return models.ListSubscriptionAPI(data=subscriptions)


@app.delete(
    "/subscriptions/{id}",
    status_code=status.HTTP_204_NO_CONTENT,
    responses={404: {"model": models.NotFound}},
    tags=["subscriptions"],
)
def delete_subscription(id: str):
    services.delete_subscription(id)


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
