"""POST /pricing/calculate — lane cost + duty/tax exposure for pricing engine."""

from __future__ import annotations

from fastapi import APIRouter, Query

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
def calculate_pricing(
    destination_country: str = Query(...),
    weight_g: int = Query(...),
    category_slug: str = Query(...),
    value_minor: int = Query(0),
) -> dict:
    """Return lane costs, duty rates, taxes, and landed cost for a shipment.

    Quotes both ITPS and EMS lanes (EMS may be unavailable), looks up
    destination-country duties, and computes landed cost = value + freight
    for each available lane.
    """
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
