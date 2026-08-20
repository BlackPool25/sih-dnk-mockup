"""Verification service FastAPI — port 8008 (8000 in container). MOCKED for demo."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers.verify import bindings_router, router as verify_router, trust_router

app = FastAPI(title="dnk-verification", version="0.1.0", description="Mocked verification L0/L1/L2 + liveness")

app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(verify_router)
app.include_router(trust_router)
app.include_router(bindings_router)

@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "mode": "mock", "verification_mode": "mock"}

@app.get("/")
async def root() -> dict[str, str]:
    return {"service": "dnk-verification", "mode": "mock", "verification_mode": "mock"}
