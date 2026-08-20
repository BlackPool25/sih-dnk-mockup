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
import time
import unicodedata
from datetime import date, datetime
from typing import Any

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
from app.services.cache import cache

_SEARCH_TTL_SECONDS = 300.0
_search_cache: dict[str, tuple[float, list[dict[str, Any]]]] = {}


def _normalize_query(query: str) -> str:
    return unicodedata.normalize("NFKC", query).lower().strip()

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


def _cache_read(key: str) -> Any | None:
    """Read from cache with config-version guard. Returns None on miss/stale."""
    raw = cache.get(key)
    if raw is None:
        return None
    if isinstance(raw, dict) and "v" in raw:
        if raw["v"] != cache.get_config_version():
            cache.delete(key)
            return None
        return raw["data"]
    return raw


def _cache_write(key: str, data: Any) -> None:
    """Write to cache with config-version stamp."""
    cache.set(key, {"v": cache.get_config_version(), "data": data})


# Spoken-language product words (Hindi + English) -> the seeded category
# slugs they plausibly describe.  This is the search vocabulary that lets the
# model-facing tool resolve a user's raw words ("कपड़ा" = cloth) to the
# seeded categories.  Generic words ("कपड़ा", "cloth") deliberately map to
# the whole plausible textile family — the model (or the chat
# disambiguation) picks the best one, or asks the user when it cannot.
_CATEGORY_KEYWORD_INDEX: dict[str, tuple[str, ...]] = {
    "block-printed-textiles": (
        "cloth", "fabric", "textile", "printed", "print", "saree", "sari",
        "kurti", "shirt", "shirts", "tshirt", "t-shirt", "shorts", "garment",
        "कपड़ा", "कपड़े", "वस्त्र", "कपडा", "कपडे", "साड़ी", "कुर्ती",
        "शर्ट", "टी-शर्ट", "शॉर्ट", "शॉर्ट्स", "वस्त्र",
        "ब्लॉक प्रिंट", "छपाई",
    ),
    "embroidered-bags-pouches": (
        "bag", "bags", "handbag", "pouch", "tote", "clutch", "बैग", "थैला",
        "हैंडबैग", "पाउच",
    ),
    "embroidered-home-textiles": (
        "cushion", "tablecloth", "bedspread", "embroidered", "कढ़ाई",
        "कुशन", "टेबलक्लॉथ", "कपड़ा", "कपड़े", "वस्त्र", "कपडा", "कपडे",
    ),
    "handloom-scarves-stoles": (
        "scarf", "stole", "muffler", "dupatta", "handloom", "shawl", "शॉल",
        "दुपट्टा", "कपड़ा", "कपड़े", "वस्त्र", "कपडा", "कपडे",
    ),
    "imitation-artisan-jewellery": (
        "jewellery", "jewelry", "necklace", "earring", "bangle", "आभूषण",
        "गहने", "कान की बाली",
    ),
    "jute-products": (
        "jute", "जूट", "गोनी", "जूट बैग",
    ),
    "small-brass-metalware": (
        "brass", "metalware", "diya", "bell", "idol", "पीतल", "कांस्य",
    ),
    "small-woodware": (
        "wood", "wooden", "carving", "bowl", "लकड़ी", "काष्ठ", "लकडी",
    ),
}

_KEYWORD_TO_SLUGS: dict[str, tuple[str, ...]] = {
    keyword: tuple(slug for slug, words in _CATEGORY_KEYWORD_INDEX.items() if keyword in words)
    for keywords in _CATEGORY_KEYWORD_INDEX.values()
    for keyword in keywords
}


def search_categories(query: str) -> list[dict]:
    """Find product categories whose slug, name, or spoken-language keyword
    contains the query text.

    The keyword index lets a raw user word ("कपड़ा") resolve to the seeded
    categories even though the DB stores English names — the model tool-call
    path depends on this.  Returns at most 5 rows (LIMIT in the query); each
    dict carries the category identity plus provenance.
    """
    normalized = _normalize_query(query)
    now = time.monotonic()
    entry = _search_cache.get(normalized)
    if entry is not None:
        ts, cached_val = entry
        if now - ts <= _SEARCH_TTL_SECONDS:
            return cached_val
        _search_cache.pop(normalized, None)

    cache_key = f"search_categories:{query}"
    cached = _cache_read(cache_key)
    if cached is not None:
        _search_cache[normalized] = (now, cached)
        return cached
    like = f"%{query}%"
    index_slugs = {
        slug for word, slugs in _KEYWORD_TO_SLUGS.items() if word in query for slug in slugs
    }
    filters = [
        ProductCategory.slug.ilike(like),
        ProductCategory.name.ilike(like),
    ]
    if index_slugs:
        filters.append(ProductCategory.slug.in_(index_slugs))
    with SessionLocal() as session:
        rows = session.scalars(
            select(ProductCategory)
            .where(or_(*filters))
            .order_by(ProductCategory.slug)
            .limit(SEARCH_CATEGORIES_LIMIT)
        ).all()
    result = [
        {
            "slug": row.slug,
            "name": row.name,
            "hs6_default": row.hs6_default,
            **_provenance(row),
        }
        for row in rows
    ]
    _cache_write(cache_key, result)
    _search_cache[normalized] = (now, result)
    return result


def lookup_hs_codes(category: str | None = None, hs6: str | None = None) -> list[dict]:
    """Look up HS codes, optionally scoped to one category slug and/or one
    hs6 code.

    Returns at most 10 rows (LIMIT in the query).  Each dict carries the
    code identity, its category slug, and provenance.
    """
    cache_key = f"lookup_hs_codes:{category}:{hs6}"
    cached = _cache_read(cache_key)
    if cached is not None:
        return cached
    with SessionLocal() as session:
        stmt = select(HsCode).join(ProductCategory, ProductCategory.id == HsCode.product_cat)
        if category is not None:
            stmt = stmt.where(ProductCategory.slug == category)
        if hs6 is not None:
            stmt = stmt.where(HsCode.hs6 == hs6)
        rows = session.scalars(stmt.order_by(HsCode.hs6, HsCode.id).limit(LOOKUP_HS_LIMIT)).all()
        cats = {
            c.id: c.slug
            for c in session.scalars(
                select(ProductCategory).where(ProductCategory.id.in_({r.product_cat for r in rows}))
            )
        }
    result = [
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
    _cache_write(cache_key, result)
    return result


def lookup_duty(country_iso2: str, hs6: str | None = None) -> list[dict]:
    """Duty / VAT / de-minimis rates for one market, optionally scoped to
    one hs6 code.

    Returns at most 20 rows (LIMIT in the query).  An unknown or never-seen
    country returns [] — never an error (pinned behaviour).
    """
    cache_key = f"lookup_duty:{country_iso2}:{hs6}"
    cached = _cache_read(cache_key)
    if cached is not None:
        return cached
    with SessionLocal() as session:
        stmt = select(CountryRate).where(CountryRate.country_iso2 == country_iso2)
        if hs6 is not None:
            stmt = stmt.where(CountryRate.hs6 == hs6)
        rows = session.scalars(
            stmt.order_by(CountryRate.rate_type, CountryRate.hs6, CountryRate.id).limit(
                LOOKUP_DUTY_LIMIT
            )
        ).all()
    result = [
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
    _cache_write(cache_key, result)
    return result


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
    cache_key = f"quote_lane:{country_iso2}:{weight_g}:{lane}"
    cached = _cache_read(cache_key)
    if cached is not None:
        return cached
    with SessionLocal() as session:
        row = session.scalar(
            select(Lane).where(Lane.country_iso2 == country_iso2, Lane.lane == lane)
        )
    if row is None:
        raise LookupError(f"no {lane} lane for country {country_iso2!r}")
    if row.weight_cap_g is not None and weight_g > row.weight_cap_g:
        raise ValueError(
            f"weight {weight_g}g exceeds {lane} {country_iso2} cap of {row.weight_cap_g}g"
        )
    over_first = max(0, weight_g - row.first_slab_g)
    extra_slabs = math.ceil(over_first / row.addl_slab_g)
    result = {
        "cost_minor": row.first_slab_rate_minor + extra_slabs * row.addl_slab_rate_minor,
        "weight_cap_g": row.weight_cap_g,
        "volume_free": row.volume_free,
        "transit_min_days": row.transit_min_days,
        "transit_max_days": row.transit_max_days,
        **_provenance(row),
    }
    _cache_write(cache_key, result)
    return result


def get_state_sales_tax(state_iso2: str) -> dict:
    """One US state's sales-tax record (rate, combined range, nexus).

    Raises KeyError for an unknown state_iso2 (pinned behaviour).
    """
    cache_key = f"state_sales_tax:{state_iso2}"
    cached = _cache_read(cache_key)
    if cached is not None:
        return cached
    with SessionLocal() as session:
        row = session.scalar(select(StateSalesTax).where(StateSalesTax.state_iso2 == state_iso2))
    if row is None:
        raise KeyError(f"unknown state_iso2 {state_iso2!r}")
    result = {
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
    _cache_write(cache_key, result)
    return result


def get_config_flag(key: str) -> dict:
    """One pinned config scalar with provenance.

    Raises KeyError for an unknown key (pinned behaviour).
    """
    cache_key = f"config_flag:{key}"
    cached = _cache_read(cache_key)
    if cached is not None:
        return cached
    with SessionLocal() as session:
        row = session.scalar(select(ConfigFlag).where(ConfigFlag.flag_key == key))
    if row is None:
        raise KeyError(f"unknown config flag {key!r}")
    result = {
        "flag_key": row.flag_key,
        "flag_value": row.flag_value,
        **_provenance(row),
    }
    _cache_write(cache_key, result)
    return result


__all__ = [
    "get_config_flag",
    "get_state_sales_tax",
    "lookup_duty",
    "lookup_hs_codes",
    "quote_lane",
    "search_categories",
]
