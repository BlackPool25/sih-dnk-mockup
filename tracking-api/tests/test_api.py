"""API contract tests for tracking-api (mock provider path).

Covers: register → get → events lifecycle, 404s, duplicate rejection.
Uses SQLite in-memory via DATABASE_URL override + dependency swap so no
Postgres/Redis needed. Cache functions are monkeypatched to no-ops.
"""

import os

os.environ["DATABASE_URL"] = "sqlite:///./test_tracking.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import main
from app import cache as cache_mod
from app.database import Base

TestSQLite = create_engine(
    "sqlite:///./test_tracking.db",
    connect_args={"check_same_thread": False},
)
TestSession = sessionmaker(bind=TestSQLite, autoflush=False)


@pytest.fixture()
def client(monkeypatch):
    Base.metadata.drop_all(bind=TestSQLite)
    Base.metadata.create_all(bind=TestSQLite)
    monkeypatch.setattr(cache_mod, "get_cached_shipment", lambda _tn: None)
    monkeypatch.setattr(cache_mod, "set_cached_shipment", lambda _tn, _data: None)
    monkeypatch.setattr(cache_mod, "invalidate_shipment_cache", lambda _tn: None)

    def _override_db():
        session = TestSession()
        try:
            yield session
        finally:
            session.close()

    main.app.dependency_overrides[main.get_db] = _override_db
    with TestClient(main.app) as c:
        yield c
    main.app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=TestSQLite)


def test_healthz(client):
    resp = client.get("/healthz")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}


def test_register_and_get_shipment(client):
    resp = client.post(
        "/shipments",
        json={"tracking_number": "SIH-ABC-001", "carrier": "IndiaPost"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["tracking_number"] == "SIH-ABC-001"
    assert body["carrier"] == "IndiaPost"
    assert body["status"] == "Booked"

    resp = client.get("/shipments/SIH-ABC-001")
    assert resp.status_code == 200
    assert resp.json()["tracking_number"] == "SIH-ABC-001"


def test_duplicate_register_rejected(client):
    client.post("/shipments", json={"tracking_number": "DUP-1", "carrier": "IndiaPost"})
    resp = client.post("/shipments", json={"tracking_number": "DUP-1", "carrier": "IndiaPost"})
    assert resp.status_code == 400
    assert "already registered" in resp.json()["detail"]


def test_get_unknown_shipment_404(client):
    resp = client.get("/shipments/NO-SUCH")
    assert resp.status_code == 404


def test_add_and_list_events(client):
    client.post("/shipments", json={"tracking_number": "EVT-1", "carrier": "IndiaPost"})
    resp = client.post(
        "/shipments/EVT-1/events",
        json={"status": "In Transit", "location": "Mumbai Hub"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "In Transit"

    resp = client.get("/shipments/EVT-1/events")
    assert resp.status_code == 200
    events = resp.json()
    assert len(events) == 1
    assert events[0]["status"] == "In Transit"
    assert events[0]["location"] == "Mumbai Hub"

    # shipment status updated by event
    shipment = client.get("/shipments/EVT-1").json()
    assert shipment["status"] == "In Transit"


def test_event_on_unknown_shipment_404(client):
    resp = client.post("/shipments/NOPE/events", json={"status": "In Transit"})
    assert resp.status_code == 404
