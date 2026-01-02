from fastapi import FastAPI, Request, status
from fastapi.responses import ORJSONResponse
from prometheus_fastapi_instrumentator import Instrumentator

from fastpubsub import models
from fastpubsub.api.helpers import _create_error_response
from fastpubsub.api.middlewares import log_requests
from fastpubsub.api.routers import clients, monitoring, subscriptions, topics
from fastpubsub.config import settings
from fastpubsub.exceptions import (
    AlreadyExistsError,
    InvalidClient,
    InvalidClientToken,
    NotFoundError,
    ServiceUnavailable,
)

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
    {
        "name": "clients",
        "description": "Operations with clients.",
    },
]


def create_app() -> FastAPI:
    app = FastAPI(
        title="fastpubsub",
        description="Simple pubsub system based on FastAPI and PostgreSQL.",
        debug=settings.api_debug,
        default_response_class=ORJSONResponse,
    )

    # Add middleware
    app.middleware("http")(log_requests)

    # Add exception handlers
    @app.exception_handler(AlreadyExistsError)
    def already_exists_exception_handler(request: Request, exc: AlreadyExistsError):
        return _create_error_response(models.GenericError, status.HTTP_409_CONFLICT, exc)

    @app.exception_handler(NotFoundError)
    def not_found_exception_handler(request: Request, exc: NotFoundError):
        return _create_error_response(models.GenericError, status.HTTP_404_NOT_FOUND, exc)

    @app.exception_handler(ServiceUnavailable)
    def service_unavailable_exception_handler(request: Request, exc: ServiceUnavailable):
        return _create_error_response(models.GenericError, status.HTTP_503_SERVICE_UNAVAILABLE, exc)

    @app.exception_handler(InvalidClient)
    def invalid_client_exception_handler(request: Request, exc: InvalidClient):
        return _create_error_response(models.GenericError, status.HTTP_401_UNAUTHORIZED, exc)

    @app.exception_handler(InvalidClientToken)
    def invalid_client_token_exception_handler(request: Request, exc: InvalidClientToken):
        return _create_error_response(models.GenericError, status.HTTP_403_FORBIDDEN, exc)

    # Add routers
    app.include_router(topics.router)
    app.include_router(subscriptions.router)
    app.include_router(monitoring.router)
    app.include_router(clients.router)

    # Add Prometheus instrumentation
    Instrumentator().instrument(app).expose(app)

    return app
