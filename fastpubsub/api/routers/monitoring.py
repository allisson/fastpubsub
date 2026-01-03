"""API endpoints for monitoring and health check operations."""

from fastapi import APIRouter, status

from fastpubsub import models, services
from fastpubsub.exceptions import ServiceUnavailable

router = APIRouter(tags=["monitoring"])


@router.get(
    "/liveness",
    response_model=models.HealthCheck,
    status_code=status.HTTP_200_OK,
    summary="Liveness probe",
)
async def liveness_probe():
    """Check if the application is alive.

    Simple liveness check that always returns "alive" status.
    Used by Kubernetes and other orchestration systems to determine
    if the application process is running.

    Returns:
        HealthCheck model with status "alive".
    """
    return models.HealthCheck(status="alive")


@router.get(
    "/readiness",
    response_model=models.HealthCheck,
    status_code=status.HTTP_200_OK,
    responses={503: {"model": models.GenericError}},
    summary="Readiness probe",
)
async def readiness_probe():
    """Check if the application is ready to serve traffic.

    Comprehensive health check that verifies database connectivity.
    Returns "ready" status only if all critical dependencies are available.
    Used by Kubernetes to determine if the application can handle requests.

    Returns:
        HealthCheck model with status "ready".

    Raises:
        ServiceUnavailable: If database connection fails.
    """
    try:
        is_db_ok = await services.database_ping()
        if not is_db_ok:
            raise ServiceUnavailable("database is down")
    except Exception:
        raise ServiceUnavailable("database is down") from None

    return models.HealthCheck(status="ready")
