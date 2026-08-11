"""Backend-core middleware — exception handlers and request/response interceptors."""

from app.middleware.error_handler import register_error_handlers

__all__ = [
    "register_error_handlers",
]
