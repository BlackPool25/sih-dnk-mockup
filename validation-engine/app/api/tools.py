"""GET /api/tools/* — read-only HTTP surface over the six db_tools functions.

Thin wrappers: the db_tools list/dict results are returned verbatim (they are
already JSON-safe with provenance).  Pinned negatives map to HTTP errors:
unknown lane pair -> 404, over-cap weight -> 422, unknown state/flag key ->
404.  Unknown duty country stays 200 [] — never an error.
"""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query

from app.services import db_tools

router = APIRouter(prefix="/api/tools", tags=["tools"])


@router.get("/categories")
def get_categories(query: str = Query(...)) -> list[dict]:
    """search_categories — up to 5 category rows matching the query text."""
    return db_tools.search_categories(query)


@router.get("/hs-codes")
def get_hs_codes(category: str | None = None, hs6: str | None = None) -> list[dict]:
    """lookup_hs_codes — up to 10 rows, optionally scoped by category/hs6."""
    return db_tools.lookup_hs_codes(category, hs6)


@router.get("/duty")
def get_duty(country_iso2: str = Query(...), hs6: str | None = None) -> list[dict]:
    """lookup_duty — an unknown country is 200 [] (pinned behaviour)."""
    return db_tools.lookup_duty(country_iso2, hs6)


@router.get("/lane")
def get_lane(
    country_iso2: str = Query(...),
    weight_g: int = Query(...),
    lane: str = Query("ITPS"),
) -> dict:
    """quote_lane — unknown lane pair 404, over-cap weight 422."""
    try:
        return db_tools.quote_lane(country_iso2, weight_g, lane)
    except LookupError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc


@router.get("/state-sales-tax")
def get_state_sales_tax(state_iso2: str = Query(...)) -> dict:
    """get_state_sales_tax — unknown state 404."""
    try:
        return db_tools.get_state_sales_tax(state_iso2)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


@router.get("/config-flag")
def get_config_flag(key: str = Query(...)) -> dict:
    """get_config_flag — unknown key 404."""
    try:
        return db_tools.get_config_flag(key)
    except KeyError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc


__all__ = ["router"]
