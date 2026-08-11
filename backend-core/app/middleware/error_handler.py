"""Consistent JSON error responses for all exception types.

Registers FastAPI exception handlers that normalise every error into
``{detail, status_code}`` so clients always receive a predictable shape:

- ``HTTPException`` → the status_code and detail the caller chose.
- ``RequestValidationError`` → 422 with per-field error details.
- Unhandled ``Exception`` → 500 "Internal server error"; the traceback is
  logged server-side but **never** leaked to the client.
"""

from __future__ import annotations

import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import HTTPException, RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("backend-core.error_handler")


async def _http_exception_handler(
    _request: Request,
    exc: HTTPException,
) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail, "status_code": exc.status_code},
    )


async def _validation_exception_handler(
    _request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    field_errors: list[dict[str, object]] = []
    for error in exc.errors():
        loc = error.get("loc", [])
        path = ".".join(str(p) for p in loc) if loc else "__root__"
        field_errors.append(
            {
                "field": path,
                "message": error.get("msg", "Validation error"),
                "type": error.get("type", "value_error"),
            }
        )
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "detail": field_errors,
            "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
        },
    )


async def _unhandled_exception_handler(
    _request: Request,
    exc: Exception,
) -> JSONResponse:
    logger.exception("Unhandled exception: %s", exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "detail": "Internal server error",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
        },
    )


def register_error_handlers(app: FastAPI) -> None:
    """Attach all exception handlers to a FastAPI *app* instance."""
    app.add_exception_handler(HTTPException, _http_exception_handler)
    app.add_exception_handler(RequestValidationError, _validation_exception_handler)
    app.add_exception_handler(Exception, _unhandled_exception_handler)
