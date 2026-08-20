"""Marketplace FastAPI — port 8007 (8000 in container)."""

from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.meilisearch_client import MeilisearchClient
from app.ranking import RankingInput, compute_score

app = FastAPI(title="marketplace", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_meili = MeilisearchClient()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/marketplace/feed")
async def marketplace_feed(
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> dict[str, object]:
    """Stub feed — returns empty mocked results until catalog is seeded."""
    _ = (q, limit, offset)
    return {"hits": [], "query": q, "limit": limit, "offset": offset, "mocked": True, "total": 0}


@app.get("/marketplace/metrics")
async def marketplace_metrics() -> dict[str, object]:
    """Stub metrics."""
    return {
        "total_products": 0,
        "total_listings": 0,
        "total_sales": 0,
        "mocked": True,
    }


@app.get("/marketplace/ranking/preview")
async def ranking_preview(
    trust: float = 0.5,
    freshness: float = 0.5,
    velocity: float = 0.5,
    boost: float = 0.0,
) -> dict[str, object]:
    """Preview ranking score with given signals."""
    result = compute_score(RankingInput(trust_score=trust, freshness_score=freshness, sales_velocity=velocity, manual_boost=boost))
    return {"final_score": result.final_score, "breakdown": result.breakdown, "mocked": True}


@app.get("/marketplace/search")
async def marketplace_search(q: str = "", limit: int = 20) -> dict[str, object]:
    """Meilisearch-backed search stub."""
    res = _meili.search("listings", q, limit=limit)
    return {"hits": res.hits, "query": q, "mocked": res.mocked}
