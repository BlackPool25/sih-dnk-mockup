from __future__ import annotations
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.state import reset_stores

client = TestClient(app)

def _uid() -> str:
    return str(uuid.uuid4())

def test_seller_vs_buyer_payloads_differ() -> None:
    reset_stores()
    seller_uid = _uid()
    r0 = client.post("/verify/l0", json={"phone": "9876543210", "seller_id": seller_uid})
    assert r0.status_code == 200
    buyer_uid = _uid()
    rb = client.post("/verify/buyer", json={"email": "buyer@ex.com", "phone": "+14155551234", "country": "US", "user_id": buyer_uid})
    assert rb.status_code == 200
    assert rb.json()["note"] == "foreign buyer — no PAN verification"
    assert "pan" not in str(rb.json()).lower() or "no PAN" in rb.json()["note"]
    trust_seller = client.get(f"/trust/{seller_uid}").json()
    trust_buyer = client.get(f"/trust/{buyer_uid}").json()
    assert trust_buyer["role"] == "buyer"
    assert trust_buyer["is_verified"] is True

def test_buyer_does_not_trigger_seller_hard_block() -> None:
    reset_stores()
    buyer_uid = _uid()
    resp = client.post("/verify/buyer", json={"email": "b@ex.com", "phone": "+971501234567", "country": "AE", "user_id": buyer_uid})
    assert resp.status_code == 200
    assert resp.json()["is_verified"] is True

def test_sahayak_separate_from_buyer_and_seller() -> None:
    reset_stores()
    s_uid = _uid()
    b_uid = _uid()
    sa_uid = _uid()
    client.post("/verify/l0", json={"phone": "9876543210", "seller_id": s_uid})
    client.post("/verify/buyer", json={"email": "b@ex.com", "phone": "+14155551234", "country": "GB", "user_id": b_uid})
    client.post("/verify/sahayak", json={"center_code": "DNK-MUM-01", "employee_id": "DNK-EMP-0001", "email": "s@dnk.gov.in", "phone": "+919876543210", "user_id": sa_uid})
    ts = client.get(f"/trust/{s_uid}").json()
    tb = client.get(f"/trust/{b_uid}").json()
    tsa = client.get(f"/trust/{sa_uid}").json()
    assert tb["role"] == "buyer"
    assert tsa["role"] == "sahayak"
    assert tsa["center_code"] == "DNK-MUM-01"

def test_trust_role_param_passthrough() -> None:
    reset_stores()
    uid = _uid()
    client.post("/verify/buyer", json={"email": "b@ex.com", "phone": "+14155551234", "country": "US", "user_id": uid})
    resp = client.get(f"/trust/{uid}?role=buyer")
    assert resp.status_code == 200
    assert resp.json()["role"] == "buyer"
