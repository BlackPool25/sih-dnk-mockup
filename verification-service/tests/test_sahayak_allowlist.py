from __future__ import annotations
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.state import reset_stores

client = TestClient(app)

def _uid() -> str:
    return str(uuid.uuid4())

def test_sahayak_valid_center_pass() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/sahayak", json={"center_code": "DNK-BLR-01", "employee_id": "DNK-EMP-0001", "email": "ram@dnk.gov.in", "phone": "+919876543210", "user_id": uid})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["is_verified"] is True
    assert data["trust_level"] == "L0"
    assert data["center_code"] == "DNK-BLR-01"
    assert data["provider"] == "mock_sahayak_allowlist"

def test_sahayak_allowlist_all_centers() -> None:
    reset_stores()
    for code in ["DNK-BLR-01", "DNK-DEL-01", "DNK-MUM-01", "DNK-DEL-02"]:
        uid = _uid()
        resp = client.post("/verify/sahayak", json={"center_code": code, "employee_id": "DNK-EMP-1234", "email": "a@dnk.gov.in", "phone": "+14155551234", "user_id": uid})
        assert resp.status_code == 200, resp.text

def test_sahayak_invalid_center_403() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/sahayak", json={"center_code": "DNK-XYZ-99", "employee_id": "DNK-EMP-0001", "email": "a@dnk.gov.in", "phone": "+919876543210", "user_id": uid})
    assert resp.status_code == 403, resp.text
    assert "allowlist" in resp.text.lower()

def test_sahayak_invalid_employee_id_rejected() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/sahayak", json={"center_code": "DNK-BLR-01", "employee_id": "EMP-123", "email": "a@dnk.gov.in", "phone": "+919876543210", "user_id": uid})
    assert resp.status_code == 422

def test_sahayak_email_any_for_mock_but_domain_flag() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/sahayak", json={"center_code": "DNK-DEL-01", "employee_id": "DNK-EMP-0002", "email": "test@example.com", "phone": "+919876543210", "user_id": uid})
    assert resp.status_code == 200
    assert resp.json()["email_domain_ok"] is False
    uid2 = _uid()
    resp2 = client.post("/verify/sahayak", json={"center_code": "DNK-DEL-01", "employee_id": "DNK-EMP-0003", "email": "x@dnk.gov.in", "phone": "+919876543210", "user_id": uid2})
    assert resp2.json()["email_domain_ok"] is True
