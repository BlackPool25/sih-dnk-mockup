from __future__ import annotations

import os
import uuid

import httpx

TRACKING_API_URL = os.getenv("TRACKING_API_URL", "http://tracking-api:8000").rstrip("/")
TIMEOUT_S = 5.0

_CARRIER_MAP = {
    "ITPS": "IndiaPost",
    "EMS": "EMS",
}


def _carrier_for_lane(lane: str | None) -> str:
    if lane is None:
        return "IndiaPost"
    return _CARRIER_MAP.get(lane.upper(), "IndiaPost")


def _tracking_number_for_parcel(order_id: uuid.UUID | str, parcel_id: str, article_id: str | None) -> str:
    base = (article_id or "").strip()
    if base and len(base) >= 6:
        clean = "".join(c for c in base.upper() if c.isalnum())[:10]
        if len(clean) >= 4:
            return f"{clean}-{parcel_id.upper()}"
    oid = str(order_id).replace("-", "").upper()
    prefix = oid[:8]
    suffix = parcel_id.replace("-", "").upper()[:6] or "P1"
    return f"EX{prefix}{suffix}IN"


def register_shipments_for_order(order, parcels: list[dict]) -> list[dict]:
    results: list[dict] = []
    if not parcels:
        return results
    order_id_str = str(order.id)
    article_id = getattr(order, "article_id", None)
    for parcel in parcels:
        parcel_id = parcel.get("parcel_id") if isinstance(parcel, dict) else None
        if not parcel_id:
            continue
        lane = parcel.get("lane") if isinstance(parcel, dict) else None
        carrier = _carrier_for_lane(lane)
        tracking_number = _tracking_number_for_parcel(order.id, parcel_id, article_id)
        payload = {
            "tracking_number": tracking_number,
            "carrier": carrier,
            "order_id": order_id_str,
            "parcel_id": parcel_id,
        }
        try:
            with httpx.Client(timeout=TIMEOUT_S) as client:
                resp = client.post(f"{TRACKING_API_URL}/shipments", json=payload)
                if resp.status_code in (200, 201):
                    try:
                        results.append(resp.json())
                    except Exception:
                        results.append({"tracking_number": tracking_number, "carrier": carrier})
                elif resp.status_code == 400 and "already registered" in resp.text.lower():
                    results.append({"tracking_number": tracking_number, "carrier": carrier, "status": "already_registered"})
                else:
                    resp.raise_for_status()
        except Exception:
            continue
    return results
