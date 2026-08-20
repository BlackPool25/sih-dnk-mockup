import os

os.environ["DATABASE_URL"] = "sqlite:///./test_tracking_perparcel.db"
os.environ["REDIS_URL"] = "redis://localhost:6379/0"

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import main
from app import cache as cache_mod
from app.database import Base

TestEngine = create_engine(
    "sqlite:///./test_tracking_perparcel.db",
    connect_args={"check_same_thread": False},
)
TestSession = sessionmaker(bind=TestEngine, autoflush=False)


@pytest.fixture()
def client(monkeypatch):
    Base.metadata.drop_all(bind=TestEngine)
    Base.metadata.create_all(bind=TestEngine)
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
    Base.metadata.drop_all(bind=TestEngine)


def test_split_order_registers_N_shipments_idempotent(client):
    order_id = "ORD-TEST-001"
    r1 = client.post(
        "/shipments",
        json={"tracking_number": "EXAAA111IN-parcel-1", "carrier": "IndiaPost", "order_id": order_id, "parcel_id": "parcel-1"},
    )
    assert r1.status_code == 200
    assert r1.json()["order_id"] == order_id
    assert r1.json()["parcel_id"] == "parcel-1"

    r2 = client.post(
        "/shipments",
        json={"tracking_number": "EXAAA111IN-parcel-2", "carrier": "EMS", "order_id": order_id, "parcel_id": "parcel-2"},
    )
    assert r2.status_code == 200
    assert r2.json()["parcel_id"] == "parcel-2"

    lst = client.get("/shipments", params={"order_id": order_id})
    assert lst.status_code == 200
    assert len(lst.json()) == 2

    lst2 = client.get(f"/orders/{order_id}/shipments")
    assert lst2.status_code == 200
    assert len(lst2.json()["shipments"]) == 2

    re = client.post(
        "/shipments",
        json={"tracking_number": "EXAAA111IN-parcel-1", "carrier": "IndiaPost", "order_id": order_id, "parcel_id": "parcel-1"},
    )
    assert re.status_code == 200
    assert re.json()["tracking_number"] == "EXAAA111IN-parcel-1"

    lst3 = client.get("/shipments", params={"order_id": order_id})
    assert len(lst3.json()) == 2

    filt = client.get("/shipments", params={"parcel_id": "parcel-1"})
    assert filt.status_code == 200
    assert all(s["parcel_id"] == "parcel-1" for s in filt.json())


def test_duplicate_tracking_different_parcel_rejects(client):
    order_id = "ORD-TEST-002"
    client.post(
        "/shipments",
        json={"tracking_number": "EXBBB222IN-parcel-1", "carrier": "IndiaPost", "order_id": order_id, "parcel_id": "parcel-1"},
    )
    dup = client.post(
        "/shipments",
        json={"tracking_number": "EXBBB222IN-parcel-1", "carrier": "IndiaPost", "order_id": order_id, "parcel_id": "parcel-2"},
    )
    assert dup.status_code == 400


def test_single_parcel_default_carrier_still_works(client):
    r = client.post("/shipments", json={"tracking_number": "SINGLE-001", "carrier": "IndiaPost"})
    assert r.status_code == 200
    assert r.json()["carrier"] == "IndiaPost"
    assert r.json()["order_id"] is None
    assert r.json()["parcel_id"] is None


def test_simulator_advances_per_parcel(client, monkeypatch):
    order_id = "ORD-SIM-001"
    client.post(
        "/shipments",
        json={"tracking_number": "SIM-1", "carrier": "IndiaPost", "order_id": order_id, "parcel_id": "parcel-1"},
    )
    client.post(
        "/shipments",
        json={"tracking_number": "SIM-2", "carrier": "EMS", "order_id": order_id, "parcel_id": "parcel-2"},
    )
    from app import tracking_simulator as sim_mod
    from app.database import SessionLocal as OrigSession

    def _override_session():
        s = TestSession()
        return s

    monkeypatch.setattr(sim_mod, "SessionLocal", TestSession)
    sim_mod.advance_shipments()

    e1 = client.get("/shipments/SIM-1/events")
    assert e1.status_code == 200
    assert len(e1.json()) == 1
    e2 = client.get("/shipments/SIM-2/events")
    assert e2.status_code == 200
    assert len(e2.json()) == 1

    s1 = client.get("/shipments/SIM-1").json()
    s2 = client.get("/shipments/SIM-2").json()
    assert s1["status"] != "Booked"
    assert s2["status"] != "Booked"
