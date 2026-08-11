"""FastAPI application — backend-core service.

Exposes a /health endpoint and includes the auth router with JWT middleware.
"""
from __future__ import annotations

import auth.middleware as auth_mw
from auth.routes import router as auth_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.docs import router as docs_router
from app.routers.documents import router as documents_router
from app.routers.orders import router as orders_router
from app.routers.profile import router as profile_router

# Extend public auth paths so the /health endpoint is accessible without a token.
auth_mw.PUBLIC_AUTH_PATHS = auth_mw.PUBLIC_AUTH_PATHS | {"/health"}

app = FastAPI(
    title="SIH-DNK Backend Core",
    version="0.1.0",
    description="Profiles, orders, document packs, and QR generation",
)

# CORS middleware (allow all origins in dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# JWT authentication — protects all non-public routes
app.add_middleware(auth_mw.JWTAuthMiddleware)

# Auth routes (login, register, refresh, logout, password-reset, me)
app.include_router(auth_router)

app.include_router(profile_router)

app.include_router(orders_router)

app.include_router(documents_router)

app.include_router(docs_router)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "backend-core"}
