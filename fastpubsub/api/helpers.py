"""Helper functions for API responses and error handling."""

from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def _create_error_response(model_class, status_code: int, exc: Exception):
    """Create a standardized error response JSON object.

    Args:
        model_class: Pydantic model class for the error response.
        status_code: HTTP status code for the error.
        exc: Exception instance containing the error message.

    Returns:
        JSONResponse with formatted error content and appropriate status code.
    """
    response = jsonable_encoder(model_class(detail=exc.args[0]))
    return JSONResponse(status_code=status_code, content=response)
