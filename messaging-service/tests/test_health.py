"""Health endpoint test."""

from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_returns_mocked_true() -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    data: object = resp.json()
    assert isinstance(data, dict)
    assert data["status"] == "ok"
    assert data["service"] == "messaging-service"
    assert data["mocked"] is True
