"""Buyer foreign minimal mock — no PAN required, never hard-blocked."""
from __future__ import annotations
import pytest
from httpx import ASGITransport, AsyncClient
from app.main import app
@pytest.mark.asyncio
async def test_buyer_foreign_no_pan_mock(test_buyer: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/profile/buyer", json={"name": "John Buyer", "country": "US", "phone": "+1-555-1234"}, headers={"Authorization": f"Bearer {test_buyer['token']}"})
        assert resp.status_code == 201, resp.text
        data = resp.json()
        assert data["mocked"] is True
        assert data["verification_mode"] == "mock"
        assert data["pan_required"] is False
        assert "no PAN" in data["note"]
        assert data["buyer_id"] == test_buyer["user_id"]
@pytest.mark.asyncio
async def test_buyer_get_minimal_mock(test_buyer: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/profile/buyer", headers={"Authorization": f"Bearer {test_buyer['token']}"})
        assert resp.status_code == 200, resp.text
        data = resp.json()
        assert data["mocked"] is True
        assert data["verification_mode"] == "mock"
        assert data["pan_required"] is False
@pytest.mark.asyncio
async def test_buyer_not_hard_blocked_foreign(test_buyer: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for country in ["US", "GB", "AE"]:
            resp = await client.post("/profile/buyer", json={"name": "Buyer", "country": country}, headers={"Authorization": f"Bearer {test_buyer['token']}"})
            assert resp.status_code == 201
            assert resp.json()["mocked"] is True
@pytest.mark.asyncio
async def test_seller_still_requires_pan_pattern_but_buyer_does_not(test_seller: dict[str, str], test_buyer: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/profile", json={"firm_name": "Bad PAN Co", "pan": "BAD"}, headers={"Authorization": f"Bearer {test_seller['token']}"})
        assert resp.status_code == 422
        resp2 = await client.post("/profile/buyer", json={"name": "Foreign", "country": "US"}, headers={"Authorization": f"Bearer {test_buyer['token']}"})
        assert resp2.status_code == 201
        assert resp2.json()["pan_required"] is False
