"""FastAPI application — backend-core service.

Exposes a /health endpoint and includes the auth router with JWT middleware.
"""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

import auth.middleware as auth_mw
from app.middleware.error_handler import register_error_handlers
from app.middleware.rate_limiter import RateLimitMiddleware
from app.routers.docs import router as docs_router
from app.routers.documents import router as documents_router
from app.routers.llm import router as llm_router
from app.routers.orders import router as orders_router
from app.routers.payments import router as payments_router
from app.routers.pricing import router as pricing_router
from app.routers.profile import router as profile_router
from app.routers.proxy import router as proxy_router
from app.routers.qr import router as qr_router
from app.routers.guidance import router as guidance_router
from app.routers.marketplace_proxy import router as marketplace_proxy_router
from app.routers.messaging_proxy import router as messaging_proxy_router
from app.routers.tracking import router as tracking_router
from app.routers.sahayak import router as sahayak_router
from app.routers.verification_proxy import router as verification_proxy_router
from auth.routes import router as auth_router

# Extend public auth paths so the /health and webhook endpoints are accessible without a token.
auth_mw.PUBLIC_AUTH_PATHS = auth_mw.PUBLIC_AUTH_PATHS | {
    "/health",
    "/payments/webhook",
    "/guidance/signup",
    "/guidance/tts",
    "/api/voice/tts/public",
    "/api/marketplace/feed",
    "/api/marketplace/metrics",
    "/api/marketplace/ranking/preview",
    "/api/marketplace/products",
}

_orig_dispatch = auth_mw.JWTAuthMiddleware.dispatch

async def _patched_dispatch(self, request, call_next):
    p = request.url.path
    if p in auth_mw.PUBLIC_AUTH_PATHS or p.startswith("/api/marketplace/products") or p.startswith("/api/marketplace/feed"):
        return await call_next(request)
    return await _orig_dispatch(self, request, call_next)

auth_mw.JWTAuthMiddleware.dispatch = _patched_dispatch

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

# Rate limiting — per-IP + per-endpoint sliding window (after auth)
app.add_middleware(RateLimitMiddleware)

# Auth routes (login, register, refresh, logout, password-reset, me)
app.include_router(auth_router)

app.include_router(profile_router)

app.include_router(orders_router)

app.include_router(documents_router)

app.include_router(docs_router)

app.include_router(qr_router)

app.include_router(llm_router)

app.include_router(pricing_router)

app.include_router(tracking_router)

app.include_router(payments_router)

app.include_router(proxy_router)

app.include_router(guidance_router)

app.include_router(marketplace_proxy_router)

app.include_router(messaging_proxy_router)

app.include_router(verification_proxy_router)

app.include_router(sahayak_router)


register_error_handlers(app)


@app.get("/health")
async def health() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy", "service": "backend-core"}
