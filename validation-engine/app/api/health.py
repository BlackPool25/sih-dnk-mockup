"""Health-check endpoint.

GET /health — checks PostgreSQL (SELECT 1) and Redis (PING).
Returns 200 when healthy, 503 when either dependency is down.
"""

from __future__ import annotations

import os
import time

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text

from app.db import engine

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
@router.get("/")
def health_check() -> JSONResponse:
    db_healthy = True
    db_error: str | None = None
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        db_healthy = False
        db_error = str(exc)

    redis_healthy = True
    try:
        import redis

        r = redis.from_url(
            os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0"),
            decode_responses=True,
        )
        r.ping()
    except Exception:
        redis_healthy = False

    both_healthy = db_healthy and redis_healthy

    body = {
        "status": "healthy" if both_healthy else "unhealthy",
        "db": "healthy" if db_healthy else f"unhealthy: {db_error}",
        "redis": "healthy" if redis_healthy else "unhealthy",
        "timestamp": time.time(),
    }

    return JSONResponse(
        content=body,
        status_code=200 if both_healthy else 503,
    )
