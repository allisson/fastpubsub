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
    return models.HealthCheck(status="alive")


@router.get(
    "/readiness",
    response_model=models.HealthCheck,
    status_code=status.HTTP_200_OK,
    responses={503: {"model": models.GenericError}},
    summary="Readiness probe",
)
async def readiness_probe():
    try:
        is_db_ok = await services.database_ping()
        if not is_db_ok:
            raise ServiceUnavailable("database is down")
    except Exception:
        raise ServiceUnavailable("database is down") from None

    return models.HealthCheck(status="ready")
