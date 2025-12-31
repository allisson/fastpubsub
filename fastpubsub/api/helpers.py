from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def _create_error_response(model_class, status_code: int, exc: Exception):
    """Helper to create error responses."""
    response = jsonable_encoder(model_class(detail=exc.args[0]))
    return JSONResponse(status_code=status_code, content=response)
