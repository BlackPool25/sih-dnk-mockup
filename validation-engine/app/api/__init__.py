"""FastAPI app for the SIH DNK Validation Engine.

Lifespan loads dotenv and verifies DB connectivity on startup.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from dotenv import load_dotenv
from fastapi import FastAPI
from sqlalchemy import text

from app.db import engine

load_dotenv()


@asynccontextmanager
async def _lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    """Verify DB connectivity on startup; clean up on shutdown."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception as exc:
        raise RuntimeError(f"Startup DB connectivity check failed: {exc}") from exc
    yield
    engine.dispose()


app = FastAPI(
    title="SIH DNK Validation Engine",
    version="0.1.0",
    lifespan=_lifespan,
)

from app.api.docs import router as docs_router
from app.api.health import router as health_router
from app.api.orders import router as orders_router
from app.api.pricing import router as pricing_router
from app.api.validate import router as validate_router

app.include_router(docs_router)
app.include_router(health_router)
app.include_router(orders_router)
app.include_router(pricing_router)
app.include_router(validate_router)
