"""Sahayak scan history — persistent DB storage for QR scans.

POST /sahayak/scans — record a scan (sahayak/dnk only)
GET  /sahayak/scans — list scans for the authenticated sahayak (RLS)
GET  /sahayak/scans/{order_id} — single scan or 404 (RLS)
"""

from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from sqlalchemy import select

from app.models.sahayak_scan import SahayakScan
from auth.deps import get_current_user, require_role
from storage.db import get_session

router = APIRouter(prefix="/sahayak", tags=["sahayak"])


def _extract_order_id(payload: dict[str, Any]) -> str | None:
    for key in ("order_id", "orderId", "orderID", "payload_orderId"):
        if key in payload and isinstance(payload[key], str) and payload[key].strip():
            return payload[key].strip()
    return None


def _scan_to_dict(scan: SahayakScan) -> dict[str, Any]:
    return {
        "id": str(scan.id),
        "order_id": scan.order_id,
        "scanned_at": scan.scanned_at.isoformat() if scan.scanned_at else None,
        "lane_meta": scan.lane_meta,
        "sahayak_user_id": str(scan.sahayak_user_id),
    }


@router.post(
    "/scans",
    status_code=201,
    dependencies=[Depends(get_current_user), Depends(require_role("sahayak", "dnk"))],
)
async def create_scan(request: Request, body: dict[str, Any]) -> dict[str, Any]:
    user = request.state.user
    user_id = str(user["user_id"])

    order_id = _extract_order_id(body)
    if not order_id:
        raise HTTPException(status_code=422, detail="order_id or orderId is required")
    if len(order_id) > 64:
        raise HTTPException(status_code=422, detail="order_id too long (max 64)")

    lane_meta = body.get("lane_meta")
    if lane_meta is not None and not isinstance(lane_meta, dict):
        raise HTTPException(status_code=422, detail="lane_meta must be object")

    async with get_session()() as session:
        scan = SahayakScan(
            sahayak_user_id=uuid.UUID(user_id),
            order_id=order_id,
            lane_meta=lane_meta,
        )
        session.add(scan)
        await session.commit()
        await session.refresh(scan)
        return _scan_to_dict(scan)


@router.get(
    "/scans",
    dependencies=[Depends(get_current_user), Depends(require_role("sahayak", "dnk"))],
)
async def list_scans(
    request: Request,
    limit: int = Query(50, ge=1, le=200),
) -> list[dict[str, Any]]:
    user = request.state.user
    user_id = str(user["user_id"])
    async with get_session()() as session:
        result = await session.execute(
            select(SahayakScan)
            .where(SahayakScan.sahayak_user_id == uuid.UUID(user_id))
            .order_by(SahayakScan.scanned_at.desc(), SahayakScan.id.desc())
            .limit(limit)
        )
        rows = result.scalars().all()
        return [_scan_to_dict(r) for r in rows]


@router.get(
    "/scans/{order_id}",
    dependencies=[Depends(get_current_user), Depends(require_role("sahayak", "dnk"))],
)
async def get_scan(request: Request, order_id: str) -> dict[str, Any]:
    user = request.state.user
    user_id = str(user["user_id"])
    async with get_session()() as session:
        result = await session.execute(
            select(SahayakScan)
            .where(
                SahayakScan.sahayak_user_id == uuid.UUID(user_id),
                SahayakScan.order_id == order_id,
            )
            .order_by(SahayakScan.scanned_at.desc())
            .limit(1)
        )
        row = result.scalar_one_or_none()
        if row is None:
            raise HTTPException(status_code=404, detail="Scan not found")
        return _scan_to_dict(row)
