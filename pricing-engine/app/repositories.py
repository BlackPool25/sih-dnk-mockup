from typing import Any

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import CountryRate, HsCode, Lane, ProductCategory
from app.provenance import row_provenance


def search_categories(session: Session, query: str, limit: int = 5) -> list[dict[str, Any]]:
    like = f"%{query}%"

    rows = session.scalars(
        select(ProductCategory)
        .where(
            or_(
                ProductCategory.slug.ilike(like),
                ProductCategory.name.ilike(like),
            )
        )
        .order_by(ProductCategory.slug)
        .limit(limit)
    ).all()

    return [
        {
            "slug": row.slug,
            "name": row.name,
            "hs6_default": row.hs6_default,
            "pbe_desc_template": row.pbe_desc_template,
            "certifications": row.certifications,
            "lane_fit": row.lane_fit,
            "provenance": row_provenance(row),
        }
        for row in rows
    ]


def lookup_hs_codes(
    session: Session,
    category_slug: str | None = None,
    hs6: str | None = None,
    limit: int = 10,
) -> list[dict[str, Any]]:
    stmt = select(HsCode, ProductCategory.slug).join(
        ProductCategory,
        ProductCategory.id == HsCode.product_cat,
    )

    if category_slug is not None:
        stmt = stmt.where(ProductCategory.slug == category_slug)
    if hs6 is not None:
        stmt = stmt.where(HsCode.hs6 == hs6)

    rows = session.execute(
        stmt.order_by(HsCode.hs6, HsCode.id).limit(limit)
    ).all()

    return [
        {
            "hs6": hs_code.hs6,
            "itc_hs_8": hs_code.itc_hs_8,
            "hts_10": hs_code.hts_10,
            "description": hs_code.description,
            "category_slug": slug,
            "provenance": row_provenance(hs_code),
        }
        for hs_code, slug in rows
    ]


def lookup_country_rates(
    session: Session,
    country_iso2: str,
    hs6: str | None = None,
    limit: int = 20,
) -> list[dict[str, Any]]:
    stmt = select(CountryRate).where(CountryRate.country_iso2 == country_iso2)

    if hs6 is not None:
        stmt = stmt.where(CountryRate.hs6 == hs6)

    rows = session.scalars(
        stmt.order_by(CountryRate.rate_type, CountryRate.hs6, CountryRate.id).limit(limit)
    ).all()

    return [
        {
            "country_iso2": row.country_iso2,
            "hs6": row.hs6,
            "rate_type": row.rate_type,
            "rate_pct": str(row.rate_pct) if row.rate_pct is not None else None,
            "amount_minor": row.amount_minor,
            "threshold_minor": row.threshold_minor,
            "currency": row.currency,
            "basis": row.basis,
            "provenance": row_provenance(row),
        }
        for row in rows
    ]


def list_lanes(session: Session, country_iso2: str) -> list[dict[str, Any]]:
    rows = session.scalars(
        select(Lane)
        .where(Lane.country_iso2 == country_iso2)
        .order_by(Lane.lane)
    ).all()

    return [_lane_to_dict(row) for row in rows]


def get_lane(session: Session, country_iso2: str, lane: str) -> dict[str, Any]:
    row = session.scalar(
        select(Lane).where(
            Lane.country_iso2 == country_iso2,
            Lane.lane == lane,
        )
    )

    if row is None:
        raise LookupError(f"no {lane} lane for country {country_iso2!r}")

    return _lane_to_dict(row)


def _lane_to_dict(row: Lane) -> dict[str, Any]:
    return {
        "lane": row.lane,
        "country_iso2": row.country_iso2,
        "first_slab_g": row.first_slab_g,
        "first_slab_rate_minor": row.first_slab_rate_minor,
        "addl_slab_g": row.addl_slab_g,
        "addl_slab_rate_minor": row.addl_slab_rate_minor,
        "weight_cap_g": row.weight_cap_g,
        "volume_free": row.volume_free,
        "divisor": row.divisor,
        "transit_min_days": row.transit_min_days,
        "transit_max_days": row.transit_max_days,
        "conflicts": row.conflicts,
        "provenance": row_provenance(row),
    }