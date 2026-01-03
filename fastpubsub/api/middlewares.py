"""HTTP middleware for request logging and monitoring."""

import time
from uuid import uuid7

from fastapi import Request

from fastpubsub.logger import get_logger

logger = get_logger(__name__)


async def log_requests(request: Request, call_next):
    """Middleware to log HTTP requests and responses with timing and request IDs.

    This middleware:
    - Generates a unique request ID for tracking
    - Logs request details at the start
    - Measures processing time
    - Logs response details including status code and timing
    - Adds request ID header to response
    - Handles and logs any exceptions during request processing

    Args:
        request: The incoming FastAPI request.
        call_next: The next middleware or endpoint to call.

    Returns:
        The processed HTTP response.

    Raises:
        Exception: Re-raises any exceptions encountered during processing.
    """
    start_time = time.perf_counter()
    request_id = str(uuid7())
    logger.info(
        "request",
        extra={
            "request.client.host": request.client.host,
            "request.method": request.method,
            "request.url.path": request.url.path,
        },
    )

    try:
        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
    except Exception as exc:
        process_time = time.perf_counter() - start_time
        logger.error(
            "request_failed",
            extra={
                "request_id": request_id,
                "error": str(exc),
                "time": f"{process_time:.4f}s",
            },
        )
        raise

    end_time = time.perf_counter()
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
