"""Verification L0→L2 mocked flow + L3 badge + trust + human gate + Cashfree bundle."""
from __future__ import annotations
import uuid
from fastapi.testclient import TestClient
from app.main import app
from app.state import reset_stores
client = TestClient(app)
def _uid() -> str:
    return str(uuid.uuid4())
def test_l0_phone_otp_mocked() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/l0", json={"phone": "9876543210", "seller_id": uid})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["trust_level"] == "L0"
    assert data["is_verified"] is False
    assert data["provider"] == "mock_otp"
    assert "provider_request_id" in data and data["provider_request_id"].startswith("mocked-")
    assert "validUpto" in data
    assert data["next_level"] == "L1"
def test_l0_invalid_phone_rejected() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/l0", json={"phone": "12345", "seller_id": uid})
    assert resp.status_code == 422
def test_l1_pan_aadhaar_digilocker_mocked() -> None:
    reset_stores()
    uid = _uid()
    client.post("/verify/l0", json={"phone": "9876543210", "seller_id": uid})
    resp = client.post("/verify/l1", json={"pan": "ABCDE1234F", "aadhaar": "123456789012", "seller_id": uid})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["trust_level"] == "L1"
    assert data["is_verified"] is False
    assert data["provider"] == "mock_digilocker"
    assert data["provider_request_id"].startswith("mocked-")
    assert data["digilocker"]["pan_status"] == "valid"
def test_l1_invalid_pan_rejected() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/l1", json={"pan": "BADPAN", "aadhaar": "123456789012", "seller_id": uid})
    assert resp.status_code == 422
def test_l2_iec_bank_penny_reverse_upi_10min() -> None:
    reset_stores()
    uid = _uid()
    client.post("/verify/l0", json={"phone": "9876543210", "seller_id": uid})
    client.post("/verify/l1", json={"pan": "ABCDE1234F", "aadhaar": "123456789012", "seller_id": uid})
    resp = client.post("/verify/l2", json={"iec": "1234567890","ad_code": "12345678901234","bank_account": "12345678901","ifsc": "SBIN0001234","seller_id": uid})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["trust_level"] == "L2"
    assert data["is_verified"] is True
    assert data["iec_view_any"]["status"] == "valid"
    assert data["bank_penny"]["penny_status"] == "credited"
    assert "reverse_penny" in data
    assert "validUpto" in data
    assert "validUpto" in data["reverse_penny"]
    assert data["reverse_upi"].startswith("mock-upi-")
    assert data["ad_code_valid"] is True
    assert data["human_gate_required"] is True
    assert len(data["ad_code"]) == 14
def test_l2_invalid_ad_code_rejected() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/verify/l2", json={"iec": "1234567890","ad_code": "123","bank_account": "12345678901","ifsc": "SBIN0001234","seller_id": uid})
    assert resp.status_code == 422
def test_liveness_badge_mocked() -> None:
    reset_stores()
    uid = _uid()
    client.post("/verify/l0", json={"phone": "9876543210", "seller_id": uid})
    client.post("/verify/l1", json={"pan": "ABCDE1234F", "aadhaar": "123456789012", "seller_id": uid})
    client.post("/verify/l2", json={"iec": "1234567890","ad_code": "12345678901234","bank_account": "12345678901","ifsc": "SBIN0001234","seller_id": uid})
    resp = client.post("/verify/liveness", json={"selfie": "base64mockselfie", "seller_id": uid})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["trust_level"] == "L3"
    assert data["liveness_badge"] is True
    assert data["is_verified"] is True
def test_trust_get_returns_level_score() -> None:
    reset_stores()
    uid = _uid()
    client.post("/verify/l0", json={"phone": "9876543210", "seller_id": uid})
    client.post("/verify/l1", json={"pan": "ABCDE1234F", "aadhaar": "123456789012", "seller_id": uid})
    client.post("/verify/l2", json={"iec": "1234567890","ad_code": "12345678901234","bank_account": "12345678901","ifsc": "SBIN0001234","seller_id": uid})
    resp = client.get(f"/trust/{uid}")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["trust_level"] == "L2"
    assert data["trust_score"] == 85
    assert data["is_verified"] is True
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
def test_bindings_confirm_human_gate_side_by_side() -> None:
    reset_stores()
    uid = _uid()
    resp = client.post("/bindings/confirm-human-gate", json={"seller_id": uid,"current_ad": "11112222333344","proposed_ad": "11112222333344","current_ifsc": "SBIN0001234","proposed_ifsc": "SBIN0001234"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["human_gate_confirmed"] is True
    assert "side_by_side" in data
    assert data["side_by_side"]["current_ad"] == "11112222333344"
def test_cashfree_bundle_mocked_never_live() -> None:
    reset_stores()
    resp = client.post("/verify/cashfree/bundle", json={"pan": "ABCDE1234F", "account_number": "12345678901", "ifsc": "SBIN0001234"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["mocked"] is True
    assert data["verification_mode"] == "mock"
    assert data["live_claim"] is False
    assert data["provider_request_id"].startswith("mocked-")
    assert "never claim live" in data["note"].lower() or "never live" in data["note"].lower()
def test_all_responses_include_verification_mode_mock() -> None:
    reset_stores()
    uid = _uid()
    r1 = client.post("/verify/l0", json={"phone": "9876543210", "seller_id": uid})
    assert r1.json()["verification_mode"] == "mock"
    r2 = client.post("/verify/l1", json={"pan": "ABCDE1234F", "aadhaar": "123456789012", "seller_id": uid})
    assert r2.json()["verification_mode"] == "mock"
    r3 = client.post("/verify/l2", json={"iec": "1234567890","ad_code": "12345678901234","bank_account": "12345678901","ifsc": "SBIN0001234","seller_id": uid})
    assert r3.json()["verification_mode"] == "mock"
    r4 = client.get(f"/trust/{uid}")
    assert r4.json()["verification_mode"] == "mock"
