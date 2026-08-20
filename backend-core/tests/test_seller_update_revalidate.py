"""SellerProfile PUT re-validates pan/ifsc/iec/pincode/phone/gstin/ad_code regex."""
from __future__ import annotations
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
BASE: dict[str, str] = {"firm_name": "Revalidate Exports","pan": "ABCDE1234F","ifsc": "SBIN0001234","iec": "1234567890","ad_code": "11112222333344","gstin": "22AAAAA0000A1Z5","pincode": "400069","phone": "9876543210","bank_account": "12345678901"}
@pytest.mark.asyncio
async def test_update_rejects_invalid_pan(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/profile", json=BASE, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert resp.status_code == 201, resp.text
        upd = await client.put("/profile", json={"pan": "BADPAN"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 422
@pytest.mark.asyncio
async def test_update_rejects_invalid_ifsc(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/profile", json=BASE, headers={"Authorization": f"Bearer {test_seller['token']}"})
        upd = await client.put("/profile", json={"ifsc": "BADIFSC"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 422
@pytest.mark.asyncio
async def test_update_rejects_invalid_iec(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/profile", json=BASE, headers={"Authorization": f"Bearer {test_seller['token']}"})
        upd = await client.put("/profile", json={"iec": "12345"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 422
@pytest.mark.asyncio
async def test_update_rejects_invalid_pincode(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/profile", json=BASE, headers={"Authorization": f"Bearer {test_seller['token']}"})
        upd = await client.put("/profile", json={"pincode": "000000"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 422
        upd2 = await client.put("/profile", json={"pincode": "4006"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd2.status_code == 422
@pytest.mark.asyncio
async def test_update_rejects_invalid_phone(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/profile", json=BASE, headers={"Authorization": f"Bearer {test_seller['token']}"})
        upd = await client.put("/profile", json={"phone": "12345"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 422
        upd2 = await client.put("/profile", json={"phone": "5234567890"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd2.status_code == 422
@pytest.mark.asyncio
async def test_update_rejects_invalid_gstin(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/profile", json=BASE, headers={"Authorization": f"Bearer {test_seller['token']}"})
        upd = await client.put("/profile", json={"gstin": "INVALIDGSTIN"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 422
@pytest.mark.asyncio
async def test_update_rejects_invalid_ad_code(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/profile", json=BASE, headers={"Authorization": f"Bearer {test_seller['token']}"})
        upd = await client.put("/profile", json={"ad_code": "123"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 422
        upd2 = await client.put("/profile", json={"ad_code": "ABCDEFGHIJKLMN"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd2.status_code == 422
@pytest.mark.asyncio
async def test_update_accepts_valid_all_fields(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        await client.post("/profile", json=BASE, headers={"Authorization": f"Bearer {test_seller['token']}"})
        upd = await client.put("/profile", json={"pan": "XYZAB5678C","pincode": "560001","phone": "9876543210","gstin": "29ABCDE1234F1Z5"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 200, upd.text
        data = upd.json()
        assert data["pan"] == "XYZAB5678C"
        assert data["pincode"] == "560001"
        assert data["is_verified"] is True
@pytest.mark.asyncio
async def test_is_verified_requires_L2(test_seller: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        minimal = {"firm_name": "Minimal Co", "pan": "ABCDE1234F"}
        resp = await client.post("/profile", json=minimal, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert resp.status_code == 201
        assert resp.json()["is_verified"] is False
        assert resp.json()["trust_level"] == "L1"
        upd = await client.put("/profile", json={"iec": "1234567890", "ad_code": "11112222333344", "ifsc": "SBIN0001234", "bank_account": "12345678901"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert upd.status_code == 200
        assert upd.json()["is_verified"] is True
        assert upd.json()["trust_level"] == "L2"
