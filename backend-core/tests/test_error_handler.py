"""Tests for error_handler middleware — consistent JSON error responses."""

from __future__ import annotations

from app.middleware.error_handler import register_error_handlers
from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel, Field

# ---------------------------------------------------------------------------
# Test app factory
# ---------------------------------------------------------------------------


def _make_app(*, exploding: bool = False) -> FastAPI:
    """Build a minimal FastAPI app with error handlers + test routes."""

    app = FastAPI()
    register_error_handlers(app)

    class Item(BaseModel):
        name: str
        price: float = Field(gt=0)

    @app.get("/http-error")
    async def http_error() -> None:
        raise HTTPException(status_code=403, detail="Not allowed")

    @app.get("/not-found")
    async def not_found() -> None:
        raise HTTPException(status_code=404, detail="Resource not found")

    @app.post("/items")
    async def create_item(item: Item) -> dict[str, str]:
        return {"name": item.name, "price": str(item.price)}

    @app.get("/boom")
    async def boom() -> None:
        raise ValueError("something went very wrong")

    if exploding:
        @app.get("/type-error")
        async def type_error() -> None:
            raise TypeError("unhashable type")  # pragma: no cover

    return app


# ---------------------------------------------------------------------------
# Tests — HTTPException
# ---------------------------------------------------------------------------


def test_http_exception_returns_status_and_detail() -> None:
    """HTTPException → {detail, status_code} matching the raised exception."""
    client = TestClient(_make_app())
    resp = client.get("/http-error")
    assert resp.status_code == 403
    body = resp.json()
    assert body == {"detail": "Not allowed", "status_code": 403}


def test_http_exception_404() -> None:
    """HTTPException(404) → 404 JSON."""
    client = TestClient(_make_app())
    resp = client.get("/not-found")
    assert resp.status_code == 404
    body = resp.json()
    assert body == {"detail": "Resource not found", "status_code": 404}


# ---------------------------------------------------------------------------
# Tests — RequestValidationError
# ---------------------------------------------------------------------------


def test_validation_error_returns_422_with_field_errors() -> None:
    """RequestValidationError → 422 with per-field error details."""
    client = TestClient(_make_app())
    resp = client.post("/items", json={"name": 123, "price": -5})
    assert resp.status_code == 422
    body = resp.json()
    assert body["status_code"] == 422
    assert isinstance(body["detail"], list)

    detail_list: list[dict] = body["detail"]
    fields = {e["field"] for e in detail_list}
    assert any(w in f for f in fields for w in ("name", "item")), (
        f"Expected 'name' or 'item' in fields, got {fields}"
    )
    assert any(w in f for f in fields for w in ("price", "item")), (
        f"Expected 'price' or 'item' in fields, got {fields}"
    )


def test_validation_error_missing_required_field() -> None:
    """Missing required field → 422 with field error."""
    client = TestClient(_make_app())
    resp = client.post("/items", json={})
    assert resp.status_code == 422
    body = resp.json()
    assert body["status_code"] == 422
    detail_items = body["detail"]
    assert isinstance(detail_items, list)
    # At least one error about missing 'name'
    fields = {e["field"] for e in detail_items}
    assert any(w in f for f in fields for w in ("name", "item", "__root__"))


def test_validation_error_invalid_json() -> None:
    """Invalid JSON body → 422."""
    client = TestClient(_make_app())
    resp = client.post(
        "/items",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )
    assert resp.status_code == 422
    body = resp.json()
    assert body["status_code"] == 422


# ---------------------------------------------------------------------------
# Tests — unhandled Exception
# ---------------------------------------------------------------------------


def test_unhandled_exception_returns_500_no_stack() -> None:
    """Unhandled Exception → 500 "Internal server error", no stack trace."""
    client = TestClient(_make_app(), raise_server_exceptions=False)
    resp = client.get("/boom")
    assert resp.status_code == 500
    body = resp.json()
    assert body == {"detail": "Internal server error", "status_code": 500}
    assert "ValueError" not in str(body)
    assert "something went very wrong" not in str(body)
    assert "traceback" not in str(body).lower()
