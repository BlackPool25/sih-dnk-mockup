"""Read-only DB tool surface for the LLM (todo-9 spec).

Exactly six curated functions — the model's ONLY way to touch the DB:

    search_categories      — find categories by slug/name
    lookup_hs_codes        — HS codes, optionally scoped by category/hs6
    lookup_duty            — duty/VAT/de-minimis rates for a market
    quote_lane             — ITPS/EMS slab-price math for one lane
    get_state_sales_tax    — one US state's sales-tax record
    get_config_flag        — one pinned config scalar with provenance

Guardrails (pinned by the plan):

- SELECT-only: every query is a SQLAlchemy ORM select against the models;
  there is deliberately NO raw-SQL path and NO generic "run this query"
  tool — that is the prompt-injection vector this module exists to prevent.
- Row caps are enforced in the query itself (LIMIT), never after the fact.
- Every result dict carries provenance (source_url, source_level,
  confidence, is_estimate, effective window) so a figure is never
  presented as fact unless the research says so.
- Negative behaviours are pinned per function: LookupError for an unknown
  lane pair, ValueError for an over-cap weight, KeyError for unknown
  state/flag keys, and [] (never an error) for an unknown duty market.

The DB is the live seeded one (no fixtures): run the tests with the
container up.
"""

from __future__ import annotations

import math
from datetime import date, datetime

from sqlalchemy import or_, select

from app.db import SessionLocal
from app.models import (
    ConfigFlag,
    CountryRate,
    HsCode,
    Lane,
    ProductCategory,
    StateSalesTax,
)

# Row caps — enforced as LIMIT inside each query.
SEARCH_CATEGORIES_LIMIT = 5
LOOKUP_HS_LIMIT = 10
LOOKUP_DUTY_LIMIT = 20

# Provenance columns present on every imported (config) table.
_PROVENANCE_KEYS = (
    "source_url",
    "source_level",
    "confidence",
    "is_estimate",
    "effective_from",
    "effective_to",
)


def _iso(value: date | datetime | None) -> str | None:
    """Render a date/datetime as an ISO string (JSON-safe for the model)."""
    if value is None:
        return None
    if isinstance(value, datetime):
        return value.isoformat()
    return value.isoformat()


def _provenance(row) -> dict:
    """Copy the row's provenance keys, dropping NULLs.

    source_url/source_level/confidence/is_estimate are NOT NULL on every
    row; the effective window is included only when set.
    """
    return {
        key: _iso(getattr(row, key))
        if key in ("effective_from", "effective_to")
        else getattr(row, key)
        for key in _PROVENANCE_KEYS
        if getattr(row, key) is not None
    }


def search_categories(query: str) -> list[dict]:
    """Find product categories whose slug or name contains the query text.

    Returns at most 5 rows (LIMIT in the query).  Each dict carries the
    category identity plus provenance.
    """
    like = f"%{query}%"
    with SessionLocal() as session:
        rows = session.scalars(
            select(ProductCategory)
            .where(
                or_(
                    ProductCategory.slug.ilike(like),
                    ProductCategory.name.ilike(like),
                )
            )
            .order_by(ProductCategory.slug)
            .limit(SEARCH_CATEGORIES_LIMIT)
        ).all()
    return [
        {
            "slug": row.slug,
            "name": row.name,
            "hs6_default": row.hs6_default,
            **_provenance(row),
        }
        for row in rows
    ]


def lookup_hs_codes(category: str | None = None, hs6: str | None = None) -> list[dict]:
    """Look up HS codes, optionally scoped to one category slug and/or one
    hs6 code.

    Returns at most 10 rows (LIMIT in the query).  Each dict carries the
    code identity, its category slug, and provenance.
    """
    with SessionLocal() as session:
        stmt = select(HsCode).join(
            ProductCategory, ProductCategory.id == HsCode.product_cat
        )
        if category is not None:
            stmt = stmt.where(ProductCategory.slug == category)
        if hs6 is not None:
            stmt = stmt.where(HsCode.hs6 == hs6)
        rows = session.scalars(
            stmt.order_by(HsCode.hs6, HsCode.id).limit(LOOKUP_HS_LIMIT)
        ).all()
        cats = {
            c.id: c.slug
            for c in session.scalars(
                select(ProductCategory).where(
                    ProductCategory.id.in_({r.product_cat for r in rows})
                )
            )
        }
    return [
        {
            "hs6": row.hs6,
            "itc_hs_8": row.itc_hs_8,
            "hts_10": row.hts_10,
            "description": row.description,
            "category_slug": cats.get(row.product_cat),
            **_provenance(row),
        }
        for row in rows
    ]


def lookup_duty(country_iso2: str, hs6: str | None = None) -> list[dict]:
    """Duty / VAT / de-minimis rates for one market, optionally scoped to
    one hs6 code.

    Returns at most 20 rows (LIMIT in the query).  An unknown or never-seen
    country returns [] — never an error (pinned behaviour).
    """
    with SessionLocal() as session:
        stmt = select(CountryRate).where(CountryRate.country_iso2 == country_iso2)
        if hs6 is not None:
            stmt = stmt.where(CountryRate.hs6 == hs6)
        rows = session.scalars(
            stmt.order_by(CountryRate.rate_type, CountryRate.hs6, CountryRate.id).limit(
                LOOKUP_DUTY_LIMIT
            )
        ).all()
    return [
        {
            "country_iso2": row.country_iso2,
            "hs6": row.hs6,
            "rate_type": row.rate_type,
            "rate_pct": float(row.rate_pct) if row.rate_pct is not None else None,
            "amount_minor": row.amount_minor,
            "threshold_minor": row.threshold_minor,
            "currency": row.currency,
            "basis": row.basis,
            **_provenance(row),
        }
        for row in rows
    ]


def quote_lane(country_iso2: str, weight_g: int, lane: str = "ITPS") -> dict:
    """Slab-price a parcel on one lane for a market.

    Pure slab math from the lanes row:

        cost_minor = first_slab_rate_minor
                     + ceil(max(0, weight_g - first_slab_g) / addl_slab_g)
                     * addl_slab_rate_minor

    Returns cost_minor plus the lane's weight cap, volumetric flag,
    transit window, and provenance.

    Raises:
        LookupError: no (country, lane) row exists.
        ValueError:  weight_cap_g is set and weight_g exceeds it.
    """
    with SessionLocal() as session:
        row = session.scalar(
            select(Lane).where(Lane.country_iso2 == country_iso2, Lane.lane == lane)
        )
    if row is None:
        raise LookupError(f"no {lane} lane for country {country_iso2!r}")
    if row.weight_cap_g is not None and weight_g > row.weight_cap_g:
        raise ValueError(
            f"weight {weight_g}g exceeds {lane} {country_iso2} "
            f"cap of {row.weight_cap_g}g"
        )
    over_first = max(0, weight_g - row.first_slab_g)
    extra_slabs = math.ceil(over_first / row.addl_slab_g)
    return {
        "cost_minor": row.first_slab_rate_minor
        + extra_slabs * row.addl_slab_rate_minor,
        "weight_cap_g": row.weight_cap_g,
        "volume_free": row.volume_free,
        "transit_min_days": row.transit_min_days,
        "transit_max_days": row.transit_max_days,
        **_provenance(row),
    }


def get_state_sales_tax(state_iso2: str) -> dict:
    """One US state's sales-tax record (rate, combined range, nexus).

    Raises KeyError for an unknown state_iso2 (pinned behaviour).
    """
    with SessionLocal() as session:
        row = session.scalar(
            select(StateSalesTax).where(StateSalesTax.state_iso2 == state_iso2)
        )
    if row is None:
        raise KeyError(f"unknown state_iso2 {state_iso2!r}")
    return {
        "state_iso2": row.state_iso2,
        "state_name": row.state_name,
        "state_rate_pct": float(row.state_rate_pct),
        "combined_min_pct": float(row.combined_min_pct),
        "combined_max_pct": float(row.combined_max_pct),
        "nexus_threshold_usd": row.nexus_threshold_usd,
        "nexus_tx_test": row.nexus_tx_test,
        "notes": row.notes,
        **_provenance(row),
    }


def get_config_flag(key: str) -> dict:
    """One pinned config scalar with provenance.

    Raises KeyError for an unknown key (pinned behaviour).
    """
    with SessionLocal() as session:
        row = session.scalar(select(ConfigFlag).where(ConfigFlag.flag_key == key))
    if row is None:
        raise KeyError(f"unknown config flag {key!r}")
    return {
        "flag_key": row.flag_key,
        "flag_value": row.flag_value,
        **_provenance(row),
    }


__all__ = [
    "get_config_flag",
    "get_state_sales_tax",
    "lookup_duty",
    "lookup_hs_codes",
    "quote_lane",
    "search_categories",
]
