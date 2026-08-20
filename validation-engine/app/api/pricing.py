"""POST /pricing/calculate — lane cost + duty/tax exposure for pricing engine."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query, Request

from app.services.db_tools import lookup_duty, quote_lane

router = APIRouter(prefix="/pricing", tags=["pricing"])


def _money_repr(minor: int) -> str:
    """Render INR minor units as a rupee string."""
    return f"₹{minor / 100:,.2f}"


def _transit_days(lane: dict) -> str:
    """Format transit window as 'min-max' or 'min+'."""
    mn = lane.get("transit_min_days")
    mx = lane.get("transit_max_days")
    if mn is not None and mx is not None:
        return f"{mn}-{mx}"
    if mn is not None:
        return f"{mn}+"
    return "—"


@router.post("/calculate")
async def calculate_pricing(
    request: Request,
    destination_country: str | None = Query(None),
    weight_g: int | None = Query(None),
    category_slug: str | None = Query(None),
    value_minor: int = Query(0),
) -> dict:
    """Return lane costs, duty rates, taxes, and landed cost for a shipment.

    Quotes both ITPS and EMS lanes (EMS may be unavailable), looks up
    destination-country duties, and computes landed cost = value + freight
    for each available lane. Accepts params via JSON body or query string.
    """
    body_data: dict = {}
    try:
        raw_body = await request.json()
        if isinstance(raw_body, dict):
            body_data = raw_body
    except Exception:
        body_data = {}

    dest = destination_country or body_data.get("destination_country") or body_data.get("destination")
    if not dest:
        raise HTTPException(status_code=422, detail="destination_country is required")

    wt = weight_g if weight_g is not None else body_data.get("weight_g")
    if wt is None:
        raise HTTPException(status_code=422, detail="weight_g is required")
    try:
        wt = int(wt)
    except (ValueError, TypeError):
        raise HTTPException(status_code=422, detail="weight_g must be an integer")

    cat = category_slug or body_data.get("category_slug") or "jute-products"
    val = value_minor if value_minor else body_data.get("value_minor", 0)
    try:
        val = int(val or 0)
    except (ValueError, TypeError):
        val = 0

    destination_country = str(dest).strip().upper()
    weight_g = wt
    category_slug = str(cat)
    value_minor = val

    # ── lane quotes ──────────────────────────────────────────────────
    itps: dict = {}
    try:
        lane_itps = quote_lane(destination_country, weight_g, lane="ITPS")
        itps = {
            "available": True,
            "cost_minor": lane_itps["cost_minor"],
            "cost_inr": _money_repr(lane_itps["cost_minor"]),
            "transit_days": _transit_days(lane_itps),
            "weight_cap_g": lane_itps.get("weight_cap_g"),
            "within_cap": True,
        }
    except (ValueError, LookupError) as exc:
        within_cap = not (isinstance(exc, ValueError) and "exceeds" in str(exc).lower())
        itps = {
            "available": False,
            "cost_minor": None,
            "cost_inr": None,
            "transit_days": None,
            "weight_cap_g": None,
            "within_cap": within_cap,
            "error": str(exc),
        }

    ems: dict = {}
    try:
        lane_ems = quote_lane(destination_country, weight_g, lane="EMS")
        ems = {
            "available": True,
            "cost_minor": lane_ems["cost_minor"],
            "cost_inr": _money_repr(lane_ems["cost_minor"]),
            "transit_days": _transit_days(lane_ems),
            "weight_cap_g": lane_ems.get("weight_cap_g"),
            "within_cap": True,
        }
    except (ValueError, LookupError) as exc:
        within_cap = not (isinstance(exc, ValueError) and "exceeds" in str(exc).lower())
        ems = {
            "available": False,
            "cost_minor": None,
            "cost_inr": None,
            "transit_days": None,
            "weight_cap_g": None,
            "within_cap": within_cap,
            "error": str(exc),
        }

    # ── duties ───────────────────────────────────────────────────────
    duties = lookup_duty(destination_country)

    # ── landed cost per lane ─────────────────────────────────────────
    landed_cost: dict[str, int | None] = {}
    if itps["available"] and itps["cost_minor"] is not None:
        landed_cost["itps"] = value_minor + itps["cost_minor"]
    else:
        landed_cost["itps"] = None
    if ems["available"] and ems["cost_minor"] is not None:
        landed_cost["ems"] = value_minor + ems["cost_minor"]
    else:
        landed_cost["ems"] = None

    return {
        "destination": destination_country,
        "weight_g": weight_g,
        "value_minor": value_minor,
        "itps": itps,
        "ems": ems,
        "duties": duties,
        "landed_cost": landed_cost,
    }
