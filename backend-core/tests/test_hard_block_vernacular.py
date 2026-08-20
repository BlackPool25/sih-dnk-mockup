"""Hard block vernacular — AD/bank mismatch freezes payouts."""
from __future__ import annotations
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
SELLER_PAYLOAD: dict[str, str] = {"firm_name": "Vernacular Exports","owner_name": "Ramesh Kumar","pan": "ABCDE1234F","bank_account": "12345678901","ifsc": "SBIN0001234","iec": "1234567890","ad_code": "11112222333344","gstin": "22AAAAA0000A1Z5","address_line1": "123 Lane","city": "Mumbai","state": "Maharashtra","pincode": "400069","phone": "9876543210"}
@pytest.mark.asyncio
async def test_hard_block_on_ad_bank_mismatch_vernacular(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/profile", json=SELLER_PAYLOAD, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["is_verified"] is True
        assert data["trust_level"] == "L2"
        upd = await client.put("/profile", json={"ad_code": "99998888777766", "ifsc": "HDFC0001234"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 422, upd.text
        detail = upd.json().get("detail", {})
        if isinstance(detail, dict):
            assert "यह खाता" in detail.get("vernacular", "") or "यह खाता" in detail.get("message", "")
            assert "e-BRC नहीं बनेगी" in detail.get("vernacular", "") or "e-BRC नहीं बनेगी" in detail.get("message", "")
            assert "side_by_side" in detail
            assert detail["side_by_side"]["current_ad"] == "11112222333344"
            assert detail["side_by_side"]["proposed_ad"] == "99998888777766"
            assert detail["payouts_frozen"] is True
        else:
            text = str(detail)
            assert "यह खाता" in text
        upd2 = await client.put("/profile", json={"ifsc": "ICIC0001234"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd2.status_code == 422
        gate = await client.post("/profile/bindings/confirm-human-gate", json={"current_ad": "11112222333344","proposed_ad": "99998888777766","current_ifsc": "SBIN0001234","proposed_ifsc": "HDFC0001234"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert gate.status_code == 200
        assert gate.json()["human_gate_confirmed"] is True
        assert gate.json()["mocked"] is True
        assert gate.json()["verification_mode"] == "mock"
        assert "side_by_side" in gate.json()
@pytest.mark.asyncio
async def test_no_hard_block_when_same_bank_ad(test_seller: dict[str, str]) -> None:
    payload = dict(SELLER_PAYLOAD)
    payload["firm_name"] = "No Block Exports"
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/profile", json=payload, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert resp.status_code == 201
        upd = await client.put("/profile", json={"firm_name": "No Block Exports Updated"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 200
        assert upd.json()["firm_name"] == "No Block Exports Updated"
