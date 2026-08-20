from __future__ import annotations
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.state import reset_stores

client = TestClient(app)

def _uid() -> str:
    return str(uuid.uuid4())

def test_buyer_foreign_no_pan_succeeds_L0() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/buyer", json={"email": "buyer@example.com", "phone": "+14155551234", "country": "US", "user_id": uid})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["provider"] == "mock_cashfree"
    assert data["trust_level"] == "L0"
    assert data["is_verified"] is True
    assert data["note"] == "foreign buyer — no PAN verification"
    assert data["country"] == "US"
    assert resp.json()["role"] == "buyer"
    trust = client.get(f"/trust/{uid}")
    assert trust.json()["is_verified"] is True
    assert trust.json()["trust_level"] == "L0"

def test_buyer_with_971_and_passport_mock() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/buyer", json={"email": "ae@buyer.ae", "phone": "+971501234567", "country": "AE", "passport_mock": "base64mock", "address": "Dubai", "user_id": uid})
    assert resp.status_code == 200
    assert resp.json()["mocked"] is True
    assert resp.json()["verification_mode"] == "mock"

def test_buyer_invalid_phone_rejected() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/buyer", json={"email": "b@x.com", "phone": "12345", "country": "US", "user_id": uid})
    assert resp.status_code == 422

def test_buyer_invalid_country_rejected() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/buyer", json={"email": "b@x.com", "phone": "+14155551234", "country": "USA", "user_id": uid})
    assert resp.status_code == 422

def test_seller_without_pan_fails_at_L1() -> None:
    reset_stores()
    uid = _uid()
    client.post("/verify/l0", json={"phone": "9876543210", "seller_id": uid})
    resp = client.post("/verify/l1", json={"pan": "BADPAN", "aadhaar": "123456789012", "seller_id": uid})
    assert resp.status_code == 422
    resp2 = client.post("/verify/l1", json={"pan": "ABCDE1234F", "aadhaar": "bad", "seller_id": uid})
    assert resp2.status_code == 422
