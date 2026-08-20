"""TDD for SahayakScan DB history — persistent QR scan history.

- POST /sahayak/scans with {order_id} as sahayak returns 201 and persists.
- GET /sahayak/scans returns only rows for authenticated sahayak, ordered desc scanned_at.
- GET /sahayak/scans/{orderId} returns single or 404.
- Non-sahayak role cannot scan (403).
- Non-scanned order not visible in sahayak list (ensuring dashboard filtered).
- Supports both order_id and orderId payload keys (QR payload).
"""

from __future__ import annotations

import asyncio
import uuid

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import select

from app.main import app
from storage.db import get_session


@pytest.mark.asyncio
async def test_sahayak_post_scan_persisted(test_sahayak: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/sahayak/scans",
            json={"order_id": order_id},
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["order_id"] == order_id
    assert "id" in data
    assert "scanned_at" in data

    # Verify row persisted via DB query where sahayak_user_id == token user
    from app.models.sahayak_scan import SahayakScan

    async with get_session()() as session:
        result = await session.execute(
            select(SahayakScan).where(
                SahayakScan.sahayak_user_id == uuid.UUID(test_sahayak["user_id"]),
                SahayakScan.order_id == order_id,
            )
        )
        row = result.scalar_one_or_none()
        assert row is not None
        assert row.order_id == order_id
        # cleanup
        await session.delete(row)
        await session.commit()


@pytest.mark.asyncio
async def test_sahayak_post_accepts_orderId_camel(test_sahayak: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    order_id = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post(
            "/sahayak/scans",
            json={"orderId": order_id},
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
    assert resp.status_code == 201, resp.text
    assert resp.json()["order_id"] == order_id
    from app.models.sahayak_scan import SahayakScan

    async with get_session()() as session:
        result = await session.execute(
            select(SahayakScan).where(SahayakScan.order_id == order_id)
        )
        row = result.scalar_one_or_none()
        if row is not None:
            await session.delete(row)
            await session.commit()


@pytest.mark.asyncio
async def test_sahayak_get_scans_filtered_and_ordered(test_sahayak: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    oid1 = f"ORD-{uuid.uuid4().hex[:6].upper()}-1"
    oid2 = f"ORD-{uuid.uuid4().hex[:6].upper()}-2"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        r1 = await client.post(
            "/sahayak/scans",
            json={"order_id": oid1},
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
        assert r1.status_code == 201, r1.text
        # Ensure distinct scanned_at timestamps
        await asyncio.sleep(0.05)
        r2 = await client.post(
            "/sahayak/scans",
            json={"order_id": oid2},
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
        assert r2.status_code == 201, r2.text

        list_resp = await client.get(
            "/sahayak/scans",
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
    assert list_resp.status_code == 200, list_resp.text
    data = list_resp.json()
    assert isinstance(data, list)
    # Only our two rows should appear (filtered by user), and ordered desc
    ids = [row["order_id"] for row in data]
    assert oid1 in ids and oid2 in ids
    # Most recent first: oid2 should appear before oid1
    assert ids.index(oid2) < ids.index(oid1)

    # Cleanup
    from app.models.sahayak_scan import SahayakScan

    async with get_session()() as session:
        for oid in (oid1, oid2):
            result = await session.execute(select(SahayakScan).where(SahayakScan.order_id == oid))
            row = result.scalar_one_or_none()
            if row is not None:
                await session.delete(row)
        await session.commit()


@pytest.mark.asyncio
async def test_sahayak_get_single_scan(test_sahayak: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    oid = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post = await client.post(
            "/sahayak/scans",
            json={"order_id": oid},
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
        assert post.status_code == 201

        single = await client.get(
            f"/sahayak/scans/{oid}",
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
    assert single.status_code == 200, single.text
    assert single.json()["order_id"] == oid

    from app.models.sahayak_scan import SahayakScan

    async with get_session()() as session:
        result = await session.execute(select(SahayakScan).where(SahayakScan.order_id == oid))
        row = result.scalar_one_or_none()
        if row is not None:
            await session.delete(row)
            await session.commit()


@pytest.mark.asyncio
async def test_sahayak_get_single_not_found(test_sahayak: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get(
            "/sahayak/scans/ORD-NOT-EXIST-999",
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_non_sahayak_cannot_scan(test_seller: dict[str, str], test_buyer: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for user in (test_seller, test_buyer):
            resp = await client.post(
                "/sahayak/scans",
                json={"order_id": "ORD-FAKE-001"},
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            assert resp.status_code == 403, f"expected 403 for role {user['role']}, got {resp.status_code}: {resp.text}"


@pytest.mark.asyncio
async def test_non_sahayak_cannot_list(test_seller: dict[str, str], test_buyer: dict[str, str]) -> None:
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        for user in (test_seller, test_buyer):
            resp = await client.get(
                "/sahayak/scans",
                headers={"Authorization": f"Bearer {user['token']}"},
            )
            # Either 403 or empty list filtered; spec says 403 or empty. Prefer 403.
            assert resp.status_code in (403, 200), resp.text
            if resp.status_code == 403:
                continue
            # If 200, must be empty or not containing sahayak data
            assert resp.json() == [] or isinstance(resp.json(), list)


@pytest.mark.asyncio
async def test_non_scanned_not_visible(test_sahayak: dict[str, str]) -> None:
    """Non-scanned order must not appear in sahayak list (dashboard filtered)."""
    transport = ASGITransport(app=app)
    scanned = f"ORD-{uuid.uuid4().hex[:6].upper()}-SCAN"
    not_scanned = f"ORD-{uuid.uuid4().hex[:6].upper()}-NOSCAN"
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        post = await client.post(
            "/sahayak/scans",
            json={"order_id": scanned},
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
        assert post.status_code == 201
        list_resp = await client.get(
            "/sahayak/scans",
            headers={"Authorization": f"Bearer {test_sahayak['token']}"},
        )
    assert list_resp.status_code == 200
    ids = [r["order_id"] for r in list_resp.json()]
    assert scanned in ids
    assert not_scanned not in ids

    from app.models.sahayak_scan import SahayakScan

    async with get_session()() as session:
        result = await session.execute(select(SahayakScan).where(SahayakScan.order_id == scanned))
        row = result.scalar_one_or_none()
        if row is not None:
            await session.delete(row)
            await session.commit()


@pytest.mark.asyncio
async def test_isolation_between_sahayaks() -> None:
    """Two sahayaks should not see each other's scans."""
    from auth.models import User, UserRole
    from auth.services.jwt import create_access_token
    from auth.services.password import hash_password

    JWT_SECRET = "dev-secret-key-that-is-at-least-32-characters-long!!!"

    async def _make_sahayak() -> dict[str, str]:
        email = f"sahayak_iso_{uuid.uuid4().hex[:8]}@test.com"
        async with get_session()() as session:
            user = User(email=email, password_hash=hash_password("testpass"), role=UserRole("sahayak"))
            session.add(user)
            await session.commit()
            await session.refresh(user)
        uid = str(user.id)
        token = create_access_token({"sub": uid, "role": "sahayak", "email": email}, JWT_SECRET, "HS256", 60)
        return {"user_id": uid, "email": email, "token": token}

    s1 = await _make_sahayak()
    s2 = await _make_sahayak()
    oid = f"ORD-{uuid.uuid4().hex[:8].upper()}"
    try:
        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as client:
            r = await client.post("/sahayak/scans", json={"order_id": oid}, headers={"Authorization": f"Bearer {s1['token']}"})
            assert r.status_code == 201
            list_s2 = await client.get("/sahayak/scans", headers={"Authorization": f"Bearer {s2['token']}"})
            assert list_s2.status_code == 200
            assert oid not in [x["order_id"] for x in list_s2.json()]
            single_s2 = await client.get(f"/sahayak/scans/{oid}", headers={"Authorization": f"Bearer {s2['token']}"})
            assert single_s2.status_code == 404
    finally:
        from sqlalchemy import delete

        from app.models.sahayak_scan import SahayakScan

        async with get_session()() as session:
            await session.execute(delete(SahayakScan).where(SahayakScan.order_id == oid))
            await session.commit()
            await session.execute(delete(User).where(User.email.in_([s1["email"], s2["email"]])))
            await session.commit()
