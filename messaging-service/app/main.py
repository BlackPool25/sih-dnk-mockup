"""Messaging service — port 8009 (8000 in container). All mocked for demo."""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.messages import router as messages_router
from app.routers.payment_mock import router as payment_mock_router
from app.routers.quotes import router as quotes_router
from app.routers.ws import router as ws_router


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncGenerator[None, None]:
    yield


app = FastAPI(title="messaging-service", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(quotes_router)
app.include_router(messages_router)
app.include_router(ws_router)
app.include_router(payment_mock_router)


@app.get("/health")
async def health() -> dict[str, object]:
    return {"status": "ok", "service": "messaging-service", "mocked": True}
